"""Pilot, calibration, and dry-run tools: one command per pilot step.

    python -m experiments.pilot <step> --backend local|ssh --config <file> [--results <dir>] ...

Steps: images, calibrate, sweep, quota-check, bottleneck, send-accuracy,
spread, dry-run. Each step writes its data to a folder of its own under
<results>/pilot (the dry run under <results>/dry-run) and prints a Markdown
block of values to copy into notes/decisions.md. No step edits
notes/decisions.md or the config. The method of each step follows "Pilot and
calibration" in implementation/spec.md. Every step goes through the backend
interface only, so the same command works on localhost and on the cloud VMs.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import functools
import json
import re
import socket
import statistics
import sys
import time
from pathlib import Path

import httpx

from experiments.backend import UNSUPPORTED
from experiments.backends import BACKENDS, make_backend
from experiments.orchestrate import (IMPLEMENTATION, SCENARIO_FOLDERS, Condition, ledger_condition, make_run_id,
                                     read_ledger, round_order, run_condition, run_loadgen, run_round, stage_dir)
from experiments.schedule import build_schedule
from plb import protocol
from plb.config import ConfigError, git_commit, load_config
from plb.images import generate_image_set
from plb.summary import nearest_rank

# A weight ratio is "small" when its share is within this of the measured
# share; the smallest such ratio wins. 0.02 keeps 10.0 and 10.4 at 1:1.
SHARE_TOLERANCE = 0.02
CLASSES = ("small", "medium", "large")


def round_weights(t1: float, t2: float, max_sum: int) -> tuple[int, int]:
    """Weights for two workers from their throughputs, as a small integer ratio with a sum of at most max_sum."""
    share = t1 / (t1 + t2)
    best = None
    for total in range(2, max_sum + 1):
        w1 = min(range(1, total), key=lambda w: abs(w / total - share))
        error = abs(w1 / total - share)
        if error <= SHARE_TOLERANCE:
            return w1, total - w1
        if best is None or error < best[0]:
            best = (error, (w1, total - w1))
    return best[1]


def propose_classes(medians: dict[str, float]) -> dict[str, list[str]]:
    """Split images into three classes at the two largest gaps between their sorted median times."""
    ordered = sorted(medians, key=medians.get)
    gaps = sorted(range(1, len(ordered)), key=lambda i: medians[ordered[i]] - medians[ordered[i - 1]])[-2:]
    first, second = sorted(gaps)
    return dict(zip(CLASSES, (ordered[:first], ordered[first:second], ordered[second:])))


def _read_csv(path: Path) -> list[dict] | None:
    try:
        with open(path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return None


def check_dry_run(root: Path, config, round_: int) -> list[str]:
    """Every problem with a dry run, one line per run and check. An empty list means PASS."""
    rows = read_ledger(root)
    problems = []
    finished = {ledger_condition(row) for row in rows if row["status"] == "finished"}
    for condition in round_order(config, round_):
        if condition not in finished:
            problems.append(f"{make_run_id(round_, condition, 1).rsplit('-a', 1)[0]}: never finished")
    runs: dict[str, list[dict]] = {}
    for row in rows:
        runs.setdefault(row["run_id"], []).append(row)
    for run_id, run_rows in runs.items():
        statuses = [row["status"] for row in run_rows]
        if statuses[-1] == "started":
            problems.append(f"{run_id}: the ledger has a started row and no end row")
        for row in run_rows:
            if row["status"] == "failed":
                problems.append(f"{run_id}: failed: {row['reason']}")
        if "finished" not in statuses:
            continue
        folder = stage_dir(root, config.stage) / SCENARIO_FOLDERS[int(run_rows[0]["scenario"])] / run_id
        if not (folder / "summary.json").exists():
            problems.append(f"{run_id}: no summary.json")
        generator, dispatcher = _read_csv(folder / "generator.csv"), _read_csv(folder / "dispatcher.csv")
        if generator is None or dispatcher is None:
            problems.append(f"{run_id}: generator.csv or dispatcher.csv is missing")
            continue
        missing = sorted({r["request_id"] for r in generator} - {r["request_id"] for r in dispatcher})
        if missing:
            more = f" and {len(missing) - 5} more" if len(missing) > 5 else ""
            problems.append(f"{run_id}: generator rows with no dispatcher row: {', '.join(missing[:5])}{more}")
    return problems


# Shared by the steps.

def _stop(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(1)


def _step_dir(args, step: str) -> Path:
    folder = args.results / "pilot" / f"{step}-{time.strftime('%Y%m%d-%H%M%S')}"
    folder.mkdir(parents=True)
    return folder


def _backend(args, config):
    return make_backend(args.backend, config, args.config)


def _one_run(args, config, root: Path, condition: Condition, run_length, round_: int = 0, attempt: int = 1,
             config_path: Path | None = None) -> Path:
    """One orchestrator run into root. Returns its folder; a failed run stops the step."""
    ok = run_condition(config, config_path or args.config, root, round_, condition, attempt,
                       _backend(args, config), run_length, load=run_loadgen)
    run_id = make_run_id(round_, condition, attempt)
    if not ok:
        _stop(f"run {run_id} failed; the reason is in {root / 'ledger.csv'}")
    return stage_dir(root, config.stage) / SCENARIO_FOLDERS[condition.scenario] / run_id


def _summary(folder: Path) -> dict:
    return json.loads((folder / "summary.json").read_text(encoding="utf-8"))


def _write_rows(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _ms(value) -> str:
    return "none" if value is None else f"{value:.1f}"


def _print_block(step: str, args, folder: Path, lines: list[str]) -> None:
    note = (" Local backend: development numbers on one machine, not pilot results."
            if args.backend == "local" else "")
    print(f"### Pilot step `{step}`, {time.strftime('%Y-%m-%d')}\n")
    print(f"Backend `{args.backend}`, config `{args.config.name}`, generator host `{socket.gethostname()}`, "
          f"data in `{folder}`.{note}\n")
    print("\n".join(lines))


def _worker_request(image, request_id: str) -> dict:
    return {protocol.REQUEST_ID: request_id, protocol.IMAGE_ID: image.image_id, protocol.SIZE_CLASS: image.size_class}


def _default_rate(config, scenario: int, index: int) -> float:
    rates = getattr(config.rates, f"scenario{scenario}")
    if rates is None:
        _stop(f"rates.scenario{scenario} is unset; pass --rate")
    return rates[index]


# The steps.

def images_step(args, config) -> None:
    """Time each image alone on worker 1 and propose three size classes."""
    folder = _step_dir(args, "images")
    rows = []
    backend = _backend(args, config)
    try:
        backend.restart("w1")
        backend.wait_healthy("w1")
        with httpx.Client(timeout=120.0) as client:
            for image in generate_image_set(config.images, config.seeds.image_set):
                for repeat in range(args.repeats):
                    reply = client.post(f"{config.addresses.workers[0]}/process", content=image.data,
                                        headers=_worker_request(image, f"pilot-{image.image_id}-{repeat}"))
                    reply.raise_for_status()
                    rows.append({"image_id": image.image_id, "size_class": image.size_class, "repeat": repeat,
                                 "processing_ms": float(reply.headers[protocol.PROCESSING_MS])})
    finally:
        backend.close()
    _write_rows(folder / "images.csv", rows)

    medians = {}
    for row in rows:
        medians.setdefault(row["image_id"], []).append(row["processing_ms"])
    medians = {image_id: statistics.median(times) for image_id, times in medians.items()}
    lines = ["| Proposed class | Images | Median of medians ms | Lowest to highest ms |", "|---|---|---|---|"]
    for name, members in propose_classes(medians).items():
        times = [medians[m] for m in members]
        lines.append(f"| {name} | {', '.join(members)} | {statistics.median(times):.1f} | "
                     f"{min(times):.1f} to {max(times):.1f} |")
    lines.append(f"\nEach image was processed alone on w1, {args.repeats} times. Classes split at the two "
                 "largest gaps between the sorted medians.")
    _print_block("images", args, folder, lines)


async def _closed_loop(url: str, jobs, images: dict, duration_s: float, in_flight: int = 2) -> float:
    """Keep in_flight requests at the worker for duration_s. Returns completions per second."""
    jobs = iter(jobs)
    done = 0
    start = time.monotonic()
    async with httpx.AsyncClient(timeout=None) as client:
        async def sender() -> None:
            nonlocal done
            while time.monotonic() - start < duration_s:
                job = next(jobs)
                reply = await client.post(url, content=images[job.image_id].data,
                                          headers=_worker_request(images[job.image_id], f"cal-{job.request_id}"))
                done += reply.status_code == 200
        await asyncio.gather(*(sender() for _ in range(in_flight)))
    return done / (time.monotonic() - start)


def calibrate_step(args, config) -> None:
    """Per scenario, each worker's throughput with that scenario's mix, two requests always in flight."""
    if config.weights.max_sum is None:
        _stop("weights.max_sum is unset; set it before calibrating")
    folder = _step_dir(args, "calibrate")
    images = {image.image_id: image for image in generate_image_set(config.images, config.seeds.image_set)}
    rows = []
    lines = ["| Scenario | w1 per s | w2 per s | Weights w1:w2 | Capacity per s | w2 quota |",
             "|---|---|---|---|---|---|"]
    for scenario in (1, 2, 3):
        # Many more image picks than a run can use, in the scenario's mix.
        jobs = build_schedule(f"calibrate:{config.seeds.schedule}:{scenario}", scenario, 100.0,
                              100.0 * args.duration, config.images)
        backend = _backend(args, config)
        try:
            if scenario == 3:
                if config.quota.cpu_percent is None and backend.verify_quota("w2") != UNSUPPORTED:
                    _stop("quota.cpu_percent is unset; set the quota before calibrating scenario 3")
                backend.apply_quota("w2", config.quota.cpu_percent, config.quota.period_ms)
            else:
                backend.clear_quota("w2")
            quota = backend.verify_quota("w2")
            for worker in ("w1", "w2"):
                backend.restart(worker)
            for worker in ("w1", "w2"):
                backend.wait_healthy(worker)
            throughput = {worker: asyncio.run(_closed_loop(f"{url}/process", jobs, images, args.duration))
                          for worker, url in zip(("w1", "w2"), config.addresses.workers)}
        finally:
            backend.close()
        w1, w2 = round_weights(throughput["w1"], throughput["w2"], config.weights.max_sum)
        capacity = throughput["w1"] + throughput["w2"]
        rows.append({"scenario": scenario, "w1_per_s": throughput["w1"], "w2_per_s": throughput["w2"],
                     "weight_w1": w1, "weight_w2": w2, "capacity_per_s": capacity, "w2_quota": json.dumps(quota)})
        lines.append(f"| {scenario} | {throughput['w1']:.2f} | {throughput['w2']:.2f} | {w1}:{w2} | "
                     f"{capacity:.2f} | {quota if isinstance(quota, str) else json.dumps(quota)} |")
    _write_rows(folder / "calibrate.csv", rows)
    lines.append(f"\nEach worker ran {args.duration:g} s with two requests always in flight. Weights are the "
                 f"smallest integer ratio within {SHARE_TOLERANCE} of each worker's share of the throughput, with a "
                 f"sum of at most {config.weights.max_sum}. Capacity is the sum of both throughputs.")
    _print_block("calibrate", args, folder, lines)


def sweep_step(args, config) -> None:
    """Step the rate up through the dispatcher."""
    root = _step_dir(args, "sweep")
    rates = args.rates or getattr(config.rates, f"scenario{args.scenario}")
    if not rates:
        _stop(f"rates.scenario{args.scenario} is unset; pass --rates")
    lines = ["| Offered per s | Achieved per s | p95 ms | Rejected | Expired | Timed out | Errors |",
             "|---|---|---|---|---|---|---|"]
    for rate in rates:
        s = _summary(_one_run(args, config, root, Condition(args.scenario, args.rule, rate), args.step_length))
        f = s["failures"]
        lines.append(f"| {rate:g} | {s['achieved_rate']:.2f} | {_ms(s['p95_ms'])} | {f.get('rejected', 0)} | "
                     f"{f.get('expired', 0)} | {f.get('timeout', 0)} | {f.get('error', 0)} |")
    lines.append(f"\nScenario {args.scenario}, rule `{args.rule}`, one run per rate.")
    _print_block("sweep", args, root, lines)


def quota_check_step(args, config) -> None:
    """Apply the quota on worker 2, run a short load, and report the throttling counters."""
    backend = _backend(args, config)
    try:
        supported = backend.verify_quota("w2") != UNSUPPORTED
    finally:
        backend.close()
    if not supported:
        _stop(f"quota-check is unsupported on the {args.backend} backend: it has no cgroups. "
                 "Run it with --backend ssh on the cloud VMs.")
    if config.quota.cpu_percent is None or config.quota.period_ms is None:
        _stop("quota.cpu_percent and quota.period_ms must be set")
    root = _step_dir(args, "quota-check")
    rate = args.rate or _default_rate(config, 3, -1)
    folder = _one_run(args, config, root, Condition(3, args.rule, rate), args.run_length)
    metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
    lines = ["| Worker | Quota | Period | nr_throttled change | throttled_usec change |", "|---|---|---|---|---|"]
    change = {}
    for worker in ("w1", "w2"):
        before, after = metadata["cpu_stat"][worker]["before"], metadata["cpu_stat"][worker]["after"]
        change[worker] = {key: after[key] - before[key] for key in ("nr_throttled", "throttled_usec")}
        quota = (f"{config.quota.cpu_percent:g}% | {config.quota.period_ms} ms" if worker == "w2" else "none | none")
        lines.append(f"| {worker} | {quota} | {change[worker]['nr_throttled']} | {change[worker]['throttled_usec']} |")
    _print_block("quota-check", args, folder, lines)
    rise = change["w2"]["nr_throttled"]
    if rise <= 0:
        _stop("\nnr_throttled did not rise on w2, so the quota did not take effect.")
    print(f"\nnr_throttled rose by {rise} on w2 during a scenario 3 run at {rate:g} per s: the quota is active.")


def _sampler_cpu(path: Path, column: str) -> tuple[float | None, float | None]:
    values = [float(row[column]) for row in _read_csv(path) or [] if row[column] != ""]
    return (statistics.mean(values), max(values)) if values else (None, None)


def bottleneck_step(args, config) -> None:
    """At one rate, check that the generator host and the dispatcher keep up."""
    root = _step_dir(args, "bottleneck")
    folder = _one_run(args, config, root, Condition(args.scenario, args.rule, args.rate), args.run_length)
    s = _summary(folder)
    limit = config.monitoring.bottleneck_cpu_percent
    lines = [f"Planned {s['planned_rate']:.2f} per s, achieved {s['achieved_rate']:.2f} per s, "
             f"rate flag {'set' if s['rate_flag'] else 'not set'}.\n",
             "| Machine | CPU measure | Mean % | Highest % | Below the limit |", "|---|---|---|---|---|"]
    for machine, sampler, column in ((f"generator host {socket.gethostname()}", "host", "cpu_total_percent"),
                                     ("dispatcher machine", "dispatcher", "cpu_total_percent"),
                                     ("dispatcher process", "dispatcher", "cpu_process_percent")):
        mean, highest = _sampler_cpu(folder / f"sampler-{sampler}.csv", column)
        below = "unknown" if highest is None or limit is None else ("yes" if highest < limit else "no")
        lines.append(f"| {machine} | {column} | {_ms(mean)} | {_ms(highest)} | {below} |")
    lines.append(f"\nLimit `monitoring.bottleneck_cpu_percent` = {limit}. Scenario {args.scenario}, rule "
                 f"`{args.rule}`. Process CPU is a percent of one CPU.")
    _print_block("bottleneck", args, folder, lines)


def send_accuracy_step(args, config) -> None:
    """Send lag with the spin-wait switch off and on, at one rate."""
    root = _step_dir(args, "send-accuracy")
    text = args.config.read_text(encoding="utf-8-sig")
    if not re.search(r"(?m)^spin_wait\s*=", text):
        _stop("the config has no generator.spin_wait line to switch")
    lines = ["| Spin-wait | Requests | Median lag ms | p95 lag ms | Highest lag ms |", "|---|---|---|---|---|"]
    for attempt, spin in ((1, "false"), (2, "true")):
        # Only the generator reads the switch; the services keep the original config.
        variant = root / f"config-spin-wait-{spin}.toml"
        variant.write_text(re.sub(r"(?m)^spin_wait\s*=.*$", f"spin_wait = {spin}", text), encoding="utf-8")
        folder = _one_run(args, config, root, Condition(args.scenario, args.rule, args.rate), args.run_length,
                          attempt=attempt, config_path=variant)
        lags = [float(row["send_lag_ms"]) for row in _read_csv(folder / "generator.csv")]
        lines.append(f"| {'on' if spin == 'true' else 'off'} | {len(lags)} | "
                     f"{_ms(statistics.median(lags) if lags else None)} | {_ms(nearest_rank(lags, 0.95))} | "
                     f"{_ms(max(lags) if lags else None)} |")
    lines.append(f"\nSend lag is the actual minus the planned send time on generator host "
                 f"`{socket.gethostname()}`. Scenario {args.scenario}, rule `{args.rule}`, {args.rate:g} per s.")
    _print_block("send-accuracy", args, root, lines)


def spread_step(args, config) -> None:
    """One condition in five rounds, with each round's own schedule; lists the per-run p95."""
    root = _step_dir(args, "spread")
    rate = args.rate or _default_rate(config, args.scenario, 1)
    condition = Condition(args.scenario, args.rule, rate)
    p95s = []
    lines = ["| Round | p95 ms | Successes |", "|---|---|---|"]
    for round_ in range(1, 6):
        s = _summary(_one_run(args, config, root, condition, args.run_length, round_=round_))
        p95s.append(s["p95_ms"])
        lines.append(f"| {round_} | {_ms(s['p95_ms'])} | {s['successes']} |")
    known = [p for p in p95s if p is not None]
    if known:
        lines.append(f"\nLowest {min(known):.1f} ms, median {statistics.median(known):.1f} ms, highest "
                     f"{max(known):.1f} ms. Scenario {args.scenario}, rule `{args.rule}`, {rate:g} per s.")
    _print_block("spread", args, root, lines)


def dry_run_step(args, config) -> None:
    """All 36 conditions once, in a shuffled order, in a dry-run folder of their own."""
    root = args.results / "dry-run" / time.strftime("%Y%m%d-%H%M%S")
    # A frozen config refuses --run-length unless the load generator knows it is a dry run.
    load = functools.partial(run_loadgen, extra=("--dry-run",)) if config.stage == "main" else run_loadgen

    def run_one(condition: Condition, attempt: int) -> bool:
        return run_condition(config, args.config, root, 0, condition, attempt, _backend(args, config),
                             args.run_length, load=load)

    run_round(config, root, 0, run_one)
    problems = check_dry_run(root, config, 0)
    print(f"Dry run in {root}, commit {git_commit(IMPLEMENTATION)[:7]}, backend {args.backend}.")
    if problems:
        print("\n".join(["FAIL", *(f"- {problem}" for problem in problems)]))
        sys.exit(1)
    print("PASS: all 36 runs finished, every generator row joins a dispatcher row, every summary computed, "
          "and the ledger is complete.")


STEPS = {"images": images_step, "calibrate": calibrate_step, "sweep": sweep_step, "quota-check": quota_check_step,
         "bottleneck": bottleneck_step, "send-accuracy": send_accuracy_step, "spread": spread_step,
         "dry-run": dry_run_step}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run one pilot step.")
    steps = parser.add_subparsers(dest="step", required=True)
    sub = {name: steps.add_parser(name, help=function.__doc__.splitlines()[0]) for name, function in STEPS.items()}
    for name, step in sub.items():
        step.add_argument("--backend", required=True, choices=sorted(BACKENDS))
        step.add_argument("--config", required=True, type=Path, help="config TOML file")
        step.add_argument("--results", default="../results", help="results folder, relative to implementation/")
        if name not in ("images", "calibrate", "sweep"):
            step.add_argument("--run-length", type=float, help="run length in seconds instead of run.length_s")
        if name not in ("images", "calibrate", "dry-run"):
            step.add_argument("--scenario", type=int, choices=(1, 2, 3), default=2)
            step.add_argument("--rule", choices=("rr", "wrr", "lur", "feedback"),
                              default="lur" if name == "spread" else "rr")
        if name in ("quota-check", "spread"):
            step.add_argument("--rate", type=float, help="requests per second; a configured rate by default")
        if name in ("bottleneck", "send-accuracy"):
            step.add_argument("--rate", type=float, required=True, help="requests per second")
    sub["images"].add_argument("--repeats", type=int, default=5, help="times each image is processed")
    sub["calibrate"].add_argument("--duration", type=float, default=60.0, help="seconds per worker and scenario")
    sub["sweep"].add_argument("--rates", type=float, nargs="+", help="rates to step through; the configured ones by default")
    sub["sweep"].add_argument("--step-length", type=float, help="run length of each step in seconds")
    args = parser.parse_args(argv)
    args.config = args.config.resolve()
    args.results = (IMPLEMENTATION / args.results).resolve()
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        parser.error(str(exc))
    STEPS[args.step](args, config)


if __name__ == "__main__":
    main()
