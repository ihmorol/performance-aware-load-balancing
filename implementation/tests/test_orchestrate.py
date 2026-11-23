import csv
import dataclasses
import json
import socket
import subprocess
from pathlib import Path

import httpx
import pytest

from experiments.backend import Backend
from experiments.backends import BACKENDS
from experiments.local_backend import LocalBackend, is_healthy
from experiments.orchestrate import Condition, run_condition, run_round
from experiments.orchestrate import main as orchestrate_main
from plb.config import RatesConfig, load_config
from plb.rows import DISPATCHER_LOG_COLUMNS, GENERATOR_LOG_COLUMNS, WORKER_LOG_COLUMNS

IMPLEMENTATION = Path(__file__).resolve().parents[1]
DEV_CONFIG = IMPLEMENTATION / "config" / "dev.toml"


class FakeBackend(Backend):
    """Records every call. Starting the service named in fail_start raises."""

    name = "fake"

    def __init__(self, fail_start=None):
        self.calls = []
        self.fail_start = fail_start
        self.cpu_readings = iter([1.0, 3.5])

    def restart(self, service, rule=None, scenario=None, rate=None, run_id=None):
        self.calls.append(("restart", service))
        if service == self.fail_start:
            raise RuntimeError(f"{service} did not start")

    def wait_healthy(self, service):
        self.calls.append(("wait_healthy", service))

    def apply_quota(self, service, cpu_percent, period_ms):
        self.calls.append(("apply_quota", service, cpu_percent, period_ms))
        return "unsupported"

    def clear_quota(self, service):
        self.calls.append(("clear_quota", service))
        return "unsupported"

    def verify_quota(self, service):
        self.calls.append(("verify_quota", service))
        return "unsupported"

    def read_cpu_stat(self, service):
        self.calls.append(("read_cpu_stat", service))
        return "unsupported"

    def start_sampler(self, name, path):
        self.calls.append(("start_sampler", name))

    def stop_sampler(self, name):
        self.calls.append(("stop_sampler", name))

    def flush(self, service, path):
        self.calls.append(("flush", service))
        columns = DISPATCHER_LOG_COLUMNS if service == "dispatcher" else WORKER_LOG_COLUMNS
        Path(path).write_text(",".join(columns) + "\n", encoding="utf-8")

    def read_dispatcher_cpu(self):
        self.calls.append(("read_dispatcher_cpu",))
        return next(self.cpu_readings)

    def close(self):
        self.calls.append(("close",))


def fake_load(config_path, target, folder, condition, round_, run_id, run_length):
    """Stands in for the load generator: writes an empty generator log."""
    (folder / "generator.csv").write_text(",".join(GENERATOR_LOG_COLUMNS) + "\n", encoding="utf-8")
    run = {"run_id": run_id, "rule": condition.rule, "scenario": condition.scenario,
           "rate": condition.rate, "round": round_, "target": target,
           "length_s": run_length or 30.0, "dropped_window_s": 1.0, "achieved_rate_tolerance": 0.05}
    (folder / "loadgen.json").write_text(json.dumps(run), encoding="utf-8")


def read_ledger(results):
    with open(results / "ledger.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def recording_run(ran):
    """A run step that only records what it was asked to run."""
    def run_one(condition, attempt):
        ran.append((condition, attempt))
        return True
    return run_one


def fake_steps(config, results, ran, load=fake_load, fail_start=None):
    """A round 1 run step doing the real run steps on a FakeBackend.

    fail_start maps (condition, attempt) to the service that fails to start.
    """
    def run_one(condition, attempt):
        ran.append((condition, attempt))
        backend = FakeBackend(fail_start=(fail_start or {}).get((condition, attempt)))
        return run_condition(config, DEV_CONFIG, results, 1, condition, attempt, backend, load=load)
    return run_one


def test_same_round_seed_gives_the_same_order_and_the_seed_is_saved(tmp_path):
    config = load_config(DEV_CONFIG)
    first, second, other_round = [], [], []

    assert run_round(config, tmp_path / "a", 1, recording_run(first))
    assert run_round(config, tmp_path / "b", 1, recording_run(second))
    run_round(config, tmp_path / "c", 2, recording_run(other_round))

    assert first == second
    assert len({condition for condition, _ in first}) == 36
    assert first != other_round
    saved = json.loads((tmp_path / "a" / "pilot" / "round-1-order.json").read_text(encoding="utf-8"))
    # dev.toml has seeds.round_order = 1.
    assert saved["seed"] == "1:1"
    assert saved["order"] == [
        {"scenario": c.scenario, "rule": c.rule, "rate": c.rate} for c, _ in first
    ]


def test_a_stopped_round_runs_only_the_unfinished_conditions_when_started_again(tmp_path):
    config = load_config(DEV_CONFIG)
    loads = []

    def load_until_ctrl_c(*args):
        # Ctrl+C arrives while the sixth run is sending its load.
        if len(loads) == 5:
            raise KeyboardInterrupt
        loads.append(args)
        fake_load(*args)

    first, second = [], []
    with pytest.raises(KeyboardInterrupt):
        run_round(config, tmp_path, 1, fake_steps(config, tmp_path, first, load=load_until_ctrl_c))
    assert run_round(config, tmp_path, 1, fake_steps(config, tmp_path, second))

    finished_first = [condition for condition, _ in first[:5]]
    interrupted = first[5][0]
    assert len(second) == 31
    assert not set(finished_first) & {condition for condition, _ in second}
    # The interrupted run has a started row, so its new run id gets attempt 2.
    assert (interrupted, 2) in second
    assert all(attempt == 1 for condition, attempt in second if condition != interrupted)
    finished = [row for row in read_ledger(tmp_path) if row["status"] == "finished"]
    assert len(finished) == 36


def test_a_run_whose_worker_fails_to_start_is_rerun_at_the_end_and_both_attempts_stay(tmp_path):
    config = load_config(DEV_CONFIG)
    broken = Condition(2, "lur", 2.0)
    ran = []

    assert run_round(config, tmp_path, 1, fake_steps(config, tmp_path, ran, fail_start={(broken, 1): "w1"}))

    assert len(ran) == 37
    assert ran[-1] == (broken, 2)
    rows = [row for row in read_ledger(tmp_path) if row["run_id"].startswith("r1-s2-lur-2-")]
    assert [(row["run_id"], row["status"]) for row in rows] == [
        ("r1-s2-lur-2-a1", "started"), ("r1-s2-lur-2-a1", "failed"),
        ("r1-s2-lur-2-a2", "started"), ("r1-s2-lur-2-a2", "finished")]
    assert "w1 did not start" in rows[1]["reason"]


def test_a_finished_round_started_again_runs_nothing_even_for_a_rate_with_many_digits(tmp_path):
    # Pilot rates are fractions of a measured capacity, so they can have many digits.
    config = dataclasses.replace(load_config(DEV_CONFIG),
                                 rates=RatesConfig(scenario1=(1.0, 6.2438195, 3.0),
                                                   scenario2=(1.0, 2.0, 3.0), scenario3=(1.0, 2.0, 3.0)))
    first, second = [], []

    assert run_round(config, tmp_path, 1, fake_steps(config, tmp_path, first))
    assert run_round(config, tmp_path, 1, fake_steps(config, tmp_path, second))

    assert len(first) == 36
    assert second == []


def test_a_run_tried_before_a_restart_is_tried_again_at_the_end_of_the_round(tmp_path):
    config = load_config(DEV_CONFIG)
    order = []
    run_round(config, tmp_path / "order", 1, recording_run(order))
    broken = order[0][0]  # the first run of the round fails to start
    loads = []

    def load_until_ctrl_c(*args):
        # Ctrl+C arrives while the third run is sending its load.
        if len(loads) == 1:
            raise KeyboardInterrupt
        loads.append(args)
        fake_load(*args)

    first, second = [], []
    with pytest.raises(KeyboardInterrupt):
        run_round(config, tmp_path, 1, fake_steps(config, tmp_path, first, load=load_until_ctrl_c,
                                                  fail_start={(broken, 1): "w1"}))
    assert run_round(config, tmp_path, 1, fake_steps(config, tmp_path, second))

    interrupted = first[2][0]
    assert [condition for condition, _ in second[-2:]] == [broken, interrupted]
    assert [condition for condition, _ in second].count(broken) == 1


def full_main_config_text():
    """dev.toml with stage main and the keys that dev.toml leaves unset, as in test_config.py."""
    text = DEV_CONFIG.read_text(encoding="utf-8")
    text = text.replace('stage = "pilot"', 'stage = "main"')
    text = text.replace("[quota]\n", "[quota]\ncpu_percent = 50.0\nperiod_ms = 100\n")
    text = text.replace("[weights]\n", "[weights]\nmax_sum = 10\n")
    return text.replace("[ssh]\n", '[ssh]\nuser = "plb"\nkey_path = "~/.ssh/plb"\n')


def git(repo, *args):
    subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", *args],
        cwd=repo, check=True, capture_output=True,
    )


def committed_repo(repo, config_text):
    repo.mkdir()
    git(repo, "init", "-q")
    (repo / "main.toml").write_text(config_text, encoding="utf-8")
    (repo / "code.py").write_text("x = 1\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "init")
    return repo / "main.toml"


def unset_value(repo):
    return committed_repo(repo, full_main_config_text().replace("ewma_weight = 0.2\n", ""))


def dirty_tree(repo):
    path = committed_repo(repo, full_main_config_text())
    (repo / "code.py").write_text("x = 2\n", encoding="utf-8")
    return path


@pytest.mark.parametrize("command", [
    ["run", "--scenario", "1", "--rule", "rr", "--rate", "1", "--round", "1"],
    ["round", "--round", "1"],
])
@pytest.mark.parametrize("broken_config, message", [
    (unset_value, "dispatcher.ewma_weight"),
    (dirty_tree, "clean git working tree"),
])
def test_a_main_stage_config_that_is_not_ready_is_refused_before_any_service_starts(
        tmp_path, monkeypatch, capsys, command, broken_config, message):
    created = []
    monkeypatch.setitem(BACKENDS, "fake", lambda config, path: created.append(path) or FakeBackend())
    config_path = broken_config(tmp_path / "repo")
    results = tmp_path / "results"

    with pytest.raises(SystemExit) as exit_info:
        orchestrate_main([*command, "--backend", "fake", "--config", str(config_path),
                          "--results", str(results)])

    assert exit_info.value.code != 0
    assert message in capsys.readouterr().err
    assert created == []
    assert not results.exists()


def test_throw_out_only_appends_a_thrown_out_row(tmp_path):
    config = load_config(DEV_CONFIG)
    run_condition(config, DEV_CONFIG, tmp_path, 1, Condition(1, "rr", 1.0), 1, FakeBackend(), load=fake_load)

    orchestrate_main(["throw-out", "--results", str(tmp_path), "--run-id", "r1-s1-rr-1-a1",
                      "--reason", "host was busy"])

    rows = read_ledger(tmp_path)
    assert [row["status"] for row in rows] == ["started", "finished", "thrown_out"]
    assert {k: rows[2][k] for k in ("stage", "round", "scenario", "rule", "rate", "attempt", "run_id", "reason")} == {
        "stage": "pilot", "round": "1", "scenario": "1", "rule": "rr", "rate": "1.0", "attempt": "1",
        "run_id": "r1-s1-rr-1-a1", "reason": "host was busy"}


def test_a_health_reply_is_ok_on_200_waits_while_warming_up_and_fails_after_a_failed_warm_up():
    assert is_healthy("w1", httpx.Response(200, json={"status": "ok"}))
    assert not is_healthy("dispatcher", httpx.Response(503, json={"status": "warming up"}))
    with pytest.raises(RuntimeError, match="dispatcher warm-up failed"):
        is_healthy("dispatcher", httpx.Response(503, json={"status": "warm-up failed"}))


def test_starting_a_service_on_a_port_something_already_listens_on_raises():
    with socket.socket() as held:
        held.bind(("127.0.0.1", 0))
        held.listen()
        port = held.getsockname()[1]
        dev = load_config(DEV_CONFIG)
        addresses = dataclasses.replace(dev.addresses, workers=(f"http://127.0.0.1:{port}", dev.addresses.workers[1]))
        backend = LocalBackend(dataclasses.replace(dev, addresses=addresses), DEV_CONFIG)
        try:
            with pytest.raises(RuntimeError, match=f"port {port}"):
                backend.start("w1")
            assert backend.services == {}
        finally:
            backend.close()


def test_scenario_3_on_a_backend_without_quota_records_unsupported(tmp_path):
    config = load_config(DEV_CONFIG)
    backend = FakeBackend()

    finished = run_condition(config, DEV_CONFIG, tmp_path, 1, Condition(3, "wrr", 2.0), 1,
                             backend, run_length=5.0, load=fake_load)

    assert finished
    folder = tmp_path / "pilot" / "scenario-3-degraded-worker" / "r1-s3-wrr-2-a1"
    metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["quota"] == "unsupported"
    assert metadata["cpu_stat"] == "unsupported"
    assert {k: metadata[k] for k in ("run_id", "stage", "backend", "round", "scenario", "rule",
                                     "rate", "attempt", "run_length_s")} == {
        "run_id": "r1-s3-wrr-2-a1", "stage": "pilot", "backend": "fake", "round": 1,
        "scenario": 3, "rule": "wrr", "rate": 2.0, "attempt": 1, "run_length_s": 5.0}
    assert metadata["seeds"] == {"image_set": 1, "schedule": 1, "round_order": 1}
    assert metadata["dispatcher_cpu_s"] == {"start": 1.0, "end": 3.5}
    assert set(metadata["step_s"]) == {"quota", "restart", "before", "load", "after"}
    assert len(metadata["commit"]) == 40 and len(metadata["config_hash"]) == 64
    assert (folder / "summary.json").exists()
    # dev.toml leaves the quota unset.
    assert ("apply_quota", "w2", None, None) in backend.calls
    assert backend.calls[-1] == ("close",)
    assert [row["status"] for row in read_ledger(tmp_path)] == ["started", "finished"]


def test_pilot_runs_go_in_their_own_folder_and_main_runs_in_the_scenario_folder(tmp_path):
    pilot = load_config(DEV_CONFIG)
    main = dataclasses.replace(pilot, stage="main")
    condition = Condition(1, "rr", 3.0)

    run_condition(pilot, DEV_CONFIG, tmp_path, 2, condition, 1, FakeBackend(), load=fake_load)
    run_condition(main, DEV_CONFIG, tmp_path, 2, condition, 1, FakeBackend(), load=fake_load)

    assert (tmp_path / "pilot" / "scenario-1-uniform" / "r2-s1-rr-3-a1" / "summary.json").exists()
    assert (tmp_path / "scenario-1-uniform" / "r2-s1-rr-3-a1" / "summary.json").exists()
    assert [row["stage"] for row in read_ledger(tmp_path)] == ["pilot", "pilot", "main", "main"]
