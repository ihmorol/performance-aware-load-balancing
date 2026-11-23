"""Run one experiment run, or a whole round of 36, through a backend.

    python -m experiments.orchestrate run --backend local --config config/dev.toml \\
        --scenario 2 --rule feedback --rate 2 --round 0 --results local/results
    python -m experiments.orchestrate round --backend local --config config/dev.toml \\
        --round 1 --run-length 5 --results local/results
    python -m experiments.orchestrate throw-out --run-id r1-s2-feedback-2-a1 \\
        --reason "..." --results local/results

The steps of one run follow "Orchestrator" in implementation/spec.md. Each
run writes a started row to <results>/ledger.csv, then a finished or failed row.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import json
import random
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from dispatcher.rules import RULES
from experiments.backend import UNSUPPORTED, Backend
from experiments.backends import BACKENDS, make_backend
from plb.config import Config, ConfigError, config_hash, git_commit, load_config
from plb.summary import summarize_run_dir

IMPLEMENTATION = Path(__file__).resolve().parents[1]
LEDGER_COLUMNS = ("timestamp_unix_s", "stage", "round", "scenario", "rule", "rate",
                  "attempt", "run_id", "status", "reason")
# The scenario folders listed in results/README.md.
SCENARIO_FOLDERS = {1: "scenario-1-uniform", 2: "scenario-2-mixed", 3: "scenario-3-degraded-worker"}
WORKERS = ("w1", "w2")
SAMPLERS = ("host", "dispatcher", "w1", "w2")


@dataclass(frozen=True)
class Condition:
    scenario: int
    rule: str
    rate: float


def make_run_id(round_: int, condition: Condition, attempt: int) -> str:
    return f"r{round_}-s{condition.scenario}-{condition.rule}-{condition.rate:g}-a{attempt}"


def stage_dir(results: Path, stage: str) -> Path:
    """Pilot data gets its own folder, so it never mixes with main runs."""
    return results / "pilot" if stage == "pilot" else results


def append_ledger(results: Path, row: dict) -> None:
    path = results / "ledger.csv"
    new = not path.exists()
    results.mkdir(parents=True, exist_ok=True)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LEDGER_COLUMNS)
        if new:
            writer.writeheader()
        writer.writerow({"timestamp_unix_s": f"{time.time():.3f}", **row})


def read_ledger(results: Path) -> list[dict]:
    path = results / "ledger.csv"
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ledger_state(results: Path, stage: str, round_: int) -> tuple[set[Condition], Counter]:
    """The conditions of a round that have finished, and the attempts started for each."""
    rows = [row for row in read_ledger(results) if row["stage"] == stage and int(row["round"]) == round_]
    finished = {ledger_condition(row) for row in rows if row["status"] == "finished"}
    # Every attempt gets its own run id and folder, also one cut off by Ctrl+C.
    attempts = Counter(ledger_condition(row) for row in rows if row["status"] == "started")
    return finished, attempts


def ledger_condition(row: dict) -> Condition:
    return Condition(int(row["scenario"]), row["rule"], float(row["rate"]))


def run_loadgen(config_path: Path, target: str, folder: Path, condition: Condition,
                round_: int, run_id: str, run_length: float | None, extra: tuple[str, ...] = ()) -> None:
    """Step 5: run the load generator and wait for it to finish. extra holds more flags, such as --dry-run."""
    command = [sys.executable, "-m", "experiments.loadgen", "--config", str(Path(config_path).resolve()),
               "--target", target, "--scenario", str(condition.scenario), "--rate", str(condition.rate),
               "--round", str(round_), "--rule", condition.rule, "--run-id", run_id, "--out", str(folder),
               *extra]
    if run_length is not None:
        command += ["--run-length", str(run_length)]
    code = subprocess.run(command, cwd=IMPLEMENTATION).returncode
    if code != 0:
        raise RuntimeError(f"load generator exited with code {code}")


def run_condition(config: Config, config_path: Path, results: Path, round_: int, condition: Condition,
                  attempt: int, backend: Backend, run_length: float | None = None,
                  load=run_loadgen) -> bool:
    """The eight steps of one run. Returns True when the run finished.

    The backend is closed at the end, whatever happened.
    """
    run_id = make_run_id(round_, condition, attempt)
    # Absolute, because the services and the load generator write into it from their own folder.
    folder = (stage_dir(results, config.stage) / SCENARIO_FOLDERS[condition.scenario] / run_id).resolve()
    ledger_row = {"stage": config.stage, "round": round_, "scenario": condition.scenario,
                  # str() keeps every digit, so resume reads back the exact rate.
                  "rule": condition.rule, "rate": str(condition.rate), "attempt": attempt,
                  "run_id": run_id}
    append_ledger(results, {**ledger_row, "status": "started", "reason": ""})
    step_s = {}
    last = time.perf_counter()

    def lap(step: str) -> None:
        nonlocal last
        now = time.perf_counter()
        step_s[step] = round(now - last, 3)
        last = now

    try:
        # Raw files are never overwritten, so an existing folder fails the run.
        folder.mkdir(parents=True)
        workers = backend.check_workers()

        if condition.scenario == 3:
            backend.apply_quota("w2", config.quota.cpu_percent, config.quota.period_ms)
            expected = {"cpu_percent": config.quota.cpu_percent, "period_ms": config.quota.period_ms}
        else:
            backend.clear_quota("w2")
            expected = "cleared"
        quota = backend.verify_quota("w2")
        if quota not in (expected, UNSUPPORTED):
            raise RuntimeError(f"w2 quota reads {quota}, expected {expected}")
        if isinstance(quota, dict):
            quota = {"w2": quota}
        lap("quota")

        # The dispatcher warms up against the workers as soon as it starts,
        # so the workers must be healthy first.
        for worker in WORKERS:
            backend.restart(worker)
        for worker in WORKERS:
            backend.wait_healthy(worker)
        backend.restart("dispatcher", rule=condition.rule, scenario=condition.scenario,
                        rate=condition.rate, run_id=run_id)
        backend.wait_healthy("dispatcher")
        lap("restart")

        cpu_stat_before = {worker: backend.read_cpu_stat(worker) for worker in WORKERS}
        dispatcher_cpu_start = backend.read_dispatcher_cpu()
        for name in SAMPLERS:
            backend.start_sampler(name, folder / f"sampler-{name}.csv")
        lap("before")

        load(config_path, f"{config.addresses.dispatcher}/process", folder, condition,
             round_, run_id, run_length)
        lap("load")

        cpu_stat_after = {worker: backend.read_cpu_stat(worker) for worker in WORKERS}
        dispatcher_cpu_end = backend.read_dispatcher_cpu()
        for name in SAMPLERS:
            backend.stop_sampler(name)
        backend.flush("dispatcher", folder / "dispatcher.csv")
        for worker in WORKERS:
            backend.flush(worker, folder / f"worker-{worker}.csv")
        lap("after")

        readings = [*cpu_stat_before.values(), *cpu_stat_after.values()]
        if UNSUPPORTED in readings:
            cpu_stat = UNSUPPORTED
        else:
            cpu_stat = {worker: {"before": cpu_stat_before[worker], "after": cpu_stat_after[worker]}
                        for worker in WORKERS}
        metadata = {
            "run_id": run_id,
            "stage": config.stage,
            "backend": backend.name,
            "round": round_,
            "scenario": condition.scenario,
            "rule": condition.rule,
            "rate": condition.rate,
            "attempt": attempt,
            "commit": git_commit(Path(config_path).parent),
            "config_hash": config_hash(config_path),
            "seeds": dataclasses.asdict(config.seeds),
            "run_length_s": run_length if run_length is not None else config.run.length_s,
            "workers": workers,
            "quota": quota,
            "cpu_stat": cpu_stat,
            "dispatcher_cpu_s": {"start": dispatcher_cpu_start, "end": dispatcher_cpu_end},
            "step_s": step_s,
        }
        (folder / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        summarize_run_dir(folder)
    except Exception as exc:
        append_ledger(results, {**ledger_row, "status": "failed", "reason": f"{type(exc).__name__}: {exc}"})
        return False
    finally:
        backend.close()
    append_ledger(results, {**ledger_row, "status": "finished", "reason": ""})
    return True


def round_conditions(config: Config) -> list[Condition]:
    """Every scenario, each with its three rates, times the four rules."""
    return [Condition(scenario, rule, rate)
            for scenario in (1, 2, 3)
            for rate in getattr(config.rates, f"scenario{scenario}")
            for rule in RULES]


def round_seed(config: Config, round_: int) -> str:
    return f"{config.seeds.round_order}:{round_}"


def round_order(config: Config, round_: int) -> list[Condition]:
    """The 36 conditions of a round, shuffled with the round's saved seed."""
    order = round_conditions(config)
    random.Random(round_seed(config, round_)).shuffle(order)
    return order


def run_round(config: Config, results: Path, round_: int, run_one) -> bool:
    """Run every condition of a round in its shuffled order.

    run_one(condition, attempt) runs one condition and returns True when it
    finished.
    """
    seed = round_seed(config, round_)
    order = round_order(config, round_)
    folder = stage_dir(results, config.stage)
    folder.mkdir(parents=True, exist_ok=True)
    saved = {"seed": seed, "order": [dataclasses.asdict(c) for c in order]}
    (folder / f"round-{round_}-order.json").write_text(json.dumps(saved, indent=2) + "\n", encoding="utf-8")

    finished, attempts = ledger_state(results, config.stage, round_)
    # A run tried before this start (failed, or cut off by Ctrl+C) waits for
    # the end of the round, like a run that fails now.
    failed = [c for c in order if c not in finished and attempts[c]]
    for condition in order:
        if condition in finished or attempts[condition]:
            continue
        attempts[condition] += 1
        if run_one(condition, attempts[condition]):
            finished.add(condition)
        else:
            failed.append(condition)
    # A failed run gets one more try, at the end of the round.
    for condition in failed:
        attempts[condition] += 1
        if run_one(condition, attempts[condition]):
            finished.add(condition)
    return all(condition in finished for condition in order)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run one experiment run or a whole round.")
    commands = parser.add_subparsers(dest="command", required=True)
    run_parser = commands.add_parser("run", help="run one condition once")
    round_parser = commands.add_parser("round", help="run the 36 conditions of a round")
    throw_parser = commands.add_parser("throw-out", help="mark a run as thrown out in the ledger")
    for sub in (run_parser, round_parser, throw_parser):
        sub.add_argument("--results", default="../results", help="results folder, relative to implementation/")
    for sub in (run_parser, round_parser):
        sub.add_argument("--backend", required=True, choices=sorted(BACKENDS))
        sub.add_argument("--config", required=True, help="config TOML file")
        sub.add_argument("--round", type=int, required=True)
        sub.add_argument("--run-length", type=float, help="run length in seconds, pilot stage only")
    run_parser.add_argument("--scenario", type=int, required=True, choices=(1, 2, 3))
    run_parser.add_argument("--rule", required=True, choices=RULES)
    run_parser.add_argument("--rate", type=float, required=True, help="requests per second")
    throw_parser.add_argument("--run-id", required=True)
    throw_parser.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    results = IMPLEMENTATION / args.results

    if args.command == "throw-out":
        rows = [row for row in read_ledger(results) if row["run_id"] == args.run_id]
        if not rows:
            parser.error(f"run id {args.run_id} is not in {results / 'ledger.csv'}")
        run = {key: rows[-1][key] for key in LEDGER_COLUMNS if key not in ("timestamp_unix_s", "status", "reason")}
        append_ledger(results, {**run, "status": "thrown_out", "reason": args.reason})
        return

    # The main-stage guards: a config with an unset value or a dirty working
    # tree is refused here, before any backend exists.
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        parser.error(str(exc))
    config_path = Path(args.config).resolve()

    if config.stage == "main" and args.run_length is not None:
        parser.error("--run-length is for the pilot stage; main runs use run.length_s")

    def run_one(condition: Condition, attempt: int) -> bool:
        backend = make_backend(args.backend, config, config_path)
        return run_condition(config, config_path, results, args.round, condition, attempt,
                             backend, args.run_length)

    if args.command == "run":
        condition = Condition(args.scenario, args.rule, args.rate)
        _, attempts = ledger_state(results, config.stage, args.round)
        finished = run_one(condition, attempts[condition] + 1)
    else:
        needed = {f"rates.scenario{s}": getattr(config.rates, f"scenario{s}") for s in (1, 2, 3)}
        needed["seeds.round_order"] = config.seeds.round_order
        unset = [key for key, value in needed.items() if value is None]
        if unset:
            parser.error(f"unset in the config: {', '.join(unset)}")
        finished = run_round(config, results, args.round, run_one)
    sys.exit(0 if finished else 1)


if __name__ == "__main__":
    main()
