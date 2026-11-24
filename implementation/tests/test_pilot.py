import csv
import dataclasses
import json
from pathlib import Path

import httpx
import pytest

from experiments import pilot
from experiments.orchestrate import (SCENARIO_FOLDERS, append_ledger, make_run_id, round_conditions, round_order,
                                     stage_dir)
from experiments.sampler import COLUMNS as SAMPLER_COLUMNS
from experiments.ssh_backend import SshBackend
from plb.config import AddressesConfig, QuotaConfig, SshConfig, load_config
from plb.rows import DISPATCHER_LOG_COLUMNS, GENERATOR_LOG_COLUMNS, WORKER_LOG_COLUMNS

IMPLEMENTATION = Path(__file__).resolve().parents[1]
DEV_CONFIG = IMPLEMENTATION / "config" / "dev.toml"
CLOUD_CONFIG = IMPLEMENTATION / "config" / "cloud.toml"


@pytest.mark.parametrize("throughputs, expected", [((10.0, 10.4), (1, 1)), ((30.0, 10.0), (3, 1)), ((10.0, 30.0), (1, 3))])
def test_calibrated_throughputs_round_to_a_small_integer_ratio(throughputs, expected):
    assert pilot.round_weights(*throughputs, max_sum=10) == expected


@pytest.mark.parametrize("max_sum", [2, 3, 5, 10])
def test_rounded_weights_never_sum_above_the_configured_maximum(max_sum):
    for t2 in (1.0, 3.3, 7.0, 19.0):
        w1, w2 = pilot.round_weights(20.0, t2, max_sum=max_sum)
        assert w1 >= 1 and w2 >= 1 and w1 + w2 <= max_sum


def test_three_clear_clusters_of_timings_give_three_classes_with_the_right_members():
    medians = {"a": 9.0, "b": 11.0, "c": 10.0, "d": 48.0, "e": 52.0, "f": 205.0, "g": 190.0}

    assert pilot.propose_classes(medians) == {"small": ["a", "c", "b"], "medium": ["d", "e"], "large": ["g", "f"]}


def write_csv(path, columns, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, restval="")
        writer.writeheader()
        writer.writerows(rows)


def complete_dry_run(root, config):
    """A dry-run folder as a finished round leaves it, with one client request per run."""
    for condition in round_conditions(config):
        run_id = make_run_id(0, condition, 1)
        row = {"stage": config.stage, "round": 0, "scenario": condition.scenario, "rule": condition.rule,
               "rate": str(condition.rate), "attempt": 1, "run_id": run_id, "reason": ""}
        append_ledger(root, {**row, "status": "started"})
        append_ledger(root, {**row, "status": "finished"})
        folder = stage_dir(root, config.stage) / SCENARIO_FOLDERS[condition.scenario] / run_id
        write_csv(folder / "generator.csv", GENERATOR_LOG_COLUMNS, [{"request_id": "r00000"}])
        write_csv(folder / "dispatcher.csv", DISPATCHER_LOG_COLUMNS,
                  [{"request_id": "warmup-w1-0", "warmup": "1"}, {"request_id": "r00000"}])
        (folder / "summary.json").write_text("{}", encoding="utf-8")
        (folder / "metadata.json").write_text(json.dumps({"cpu_stat": "unsupported"}), encoding="utf-8")


def test_the_dry_run_check_passes_a_complete_round_and_names_a_run_whose_dispatcher_log_lost_a_row(tmp_path):
    config = load_config(DEV_CONFIG)
    complete_dry_run(tmp_path, config)
    assert pilot.check_dry_run(tmp_path, config, 0) == []

    broken = make_run_id(0, round_conditions(config)[5], 1)
    folder = next(stage_dir(tmp_path, config.stage).glob(f"*/{broken}"))
    write_csv(folder / "dispatcher.csv", DISPATCHER_LOG_COLUMNS, [{"request_id": "warmup-w1-0", "warmup": "1"}])

    problems = pilot.check_dry_run(tmp_path, config, 0)
    assert problems == [f"{broken}: generator rows with no dispatcher row: r00000"]


def test_quota_check_on_the_local_backend_exits_non_zero_with_the_unsupported_message(tmp_path, capsys):
    with pytest.raises(SystemExit) as stopped:
        pilot.main(["quota-check", "--backend", "local", "--config", str(DEV_CONFIG), "--results", str(tmp_path)])

    assert stopped.value.code != 0
    assert "unsupported on the local backend" in capsys.readouterr().err


class FakeVms:
    """Command runner and HTTP transport standing in for the four cloud VMs.

    Replies to an ssh command come from the first key found in it; a list of
    replies is used up one per call. scp to this machine writes a log with
    only its header, the way an empty run would leave it.
    """

    def __init__(self, replies):
        self.calls = []
        self.replies = replies

    def run(self, argv):
        self.calls.append(argv)
        if argv[0] == "scp" and "@" not in argv[-1]:
            name = Path(argv[-1]).name
            columns = (DISPATCHER_LOG_COLUMNS if name == "dispatcher.csv" else
                       WORKER_LOG_COLUMNS if name.startswith("worker-") else SAMPLER_COLUMNS)
            write_csv(Path(argv[-1]), columns, [])
            return ""
        command = " ".join(argv)
        for key, reply in self.replies.items():
            if key in command:
                return reply.pop(0) if isinstance(reply, list) else reply
        return ""

    def transport(self):
        def handler(request):
            if request.url.path == "/admin/cpu":
                return httpx.Response(200, json={"cpu_s": 1.0})
            return httpx.Response(200, json={"status": "ok"})
        return httpx.MockTransport(handler)


def fake_load(config_path, target, folder, condition, round_, run_id, run_length):
    write_csv(folder / "generator.csv", GENERATOR_LOG_COLUMNS, [])
    run = {"run_id": run_id, "rule": condition.rule, "scenario": condition.scenario, "rate": condition.rate,
           "round": round_, "target": target, "length_s": run_length or 30.0, "dropped_window_s": 1.0,
           "achieved_rate_tolerance": 0.05}
    (folder / "loadgen.json").write_text(json.dumps(run), encoding="utf-8")


LSCPU = "CPU(s):                  1\nModel name:              AMD EPYC 7B13\n"


def cloud_steps(monkeypatch, replies):
    """Point the pilot steps at fake cloud VMs, with a real commit check and a fake load generator."""
    vms = FakeVms({"lscpu": LSCPU, "rev-parse HEAD": pilot.git_commit(IMPLEMENTATION) + "\n", **replies})
    config = dataclasses.replace(load_config(CLOUD_CONFIG), quota=QuotaConfig(cpu_percent=50.0, period_ms=100))
    monkeypatch.setattr(pilot, "load_config", lambda path: config)
    monkeypatch.setattr(pilot, "make_backend", lambda name, config, path: SshBackend(
        config, path, run=vms.run, transport=vms.transport()))
    monkeypatch.setattr(pilot, "run_loadgen", fake_load)
    return vms


def stat(throttled):
    return f"nr_periods 100\nnr_throttled {throttled}\nthrottled_usec {throttled * 1000}\n"


def test_quota_check_over_ssh_sets_and_reads_back_the_quota_and_reports_the_throttling(tmp_path, monkeypatch, capsys):
    w2_stat = "10.128.0.22 cat /sys/fs/cgroup/system.slice/plb-worker.service/cpu.stat"
    vms = cloud_steps(monkeypatch, {"cpu.max": "50000 100000\n", w2_stat: [stat(0), stat(37)],
                                    "cpu.stat": stat(0)})

    pilot.main(["quota-check", "--backend", "ssh", "--config", str(CLOUD_CONFIG), "--results", str(tmp_path),
                "--rate", "1", "--run-length", "5"])

    w2_commands = [argv[-1] for argv in vms.calls if argv[0] == "ssh" and argv[-2] == "plb@10.128.0.22"]
    applied = w2_commands.index(
        "sudo -n systemctl set-property --runtime plb-worker.service CPUQuota=50% CPUQuotaPeriodSec=100ms")
    assert w2_commands[applied + 1] == "cat /sys/fs/cgroup/system.slice/plb-worker.service/cpu.max"
    out = capsys.readouterr().out
    assert "nr_throttled rose by 37" in out
    assert "| w2 | 50% | 100 ms | 37 | 37000 |" in out


def test_dry_run_over_ssh_runs_all_36_conditions_in_its_own_folder_and_passes(tmp_path, monkeypatch, capsys):
    # The order is shuffled, so cpu.max gets the reply each run in that order expects.
    order = round_order(load_config(CLOUD_CONFIG), 0)
    vms = cloud_steps(monkeypatch, {"cpu.stat": stat(0), "cpu.max": ["50000 100000\n" if c.scenario == 3 else "max 100000\n" for c in order]})

    pilot.main(["dry-run", "--backend", "ssh", "--config", str(CLOUD_CONFIG), "--results", str(tmp_path),
                "--run-length", "3"])

    restarts = [argv[-1] for argv in vms.calls if "restart plb-dispatcher.service" in argv[-1]]
    assert [command.split("PLB_RUN_ID=")[1].split()[0] for command in restarts] == [
        make_run_id(0, condition, 1) for condition in order]
    assert len(list(tmp_path.glob("dry-run/*/ledger.csv"))) == 1
    assert not (tmp_path / "ledger.csv").exists()
    assert capsys.readouterr().out.splitlines()[-1].startswith("PASS")


def test_processing_times_per_size_class_give_median_and_nearest_rank_p95():
    rows = [{"size_class": "large", "processing_ms": ms} for ms in range(100, 120)] + [
        {"size_class": "small", "processing_ms": 5.0}, {"size_class": "small", "processing_ms": 7.0}]

    times = pilot.class_times(rows)

    assert times["large"] == {"median": 109.5, "p95": 118, "count": 20}
    assert times["small"] == {"median": 6.0, "p95": 7.0, "count": 2}


def test_dispatcher_timeout_is_c_plus_one_times_the_large_class_p95_rounded_up():
    assert pilot.dispatcher_timeout_ms(queue_capacity=4, large_p95_ms=118.3) == 592  # 591.5 rounds up


def test_replaying_processing_times_gives_the_dispatcher_estimates_and_their_jumps():
    estimates = pilot.replay_estimates([100.0, 200.0, 100.0], a=0.5)

    assert estimates == [100.0, 150.0, 125.0]  # the first sample sets the estimate
    assert pilot.jump_stats(estimates) == {"p95": 50.0, "max": 50.0}  # jumps of 50% and 16.7%


def test_the_settle_table_averages_queue_lengths_and_estimates_per_time_bucket():
    generator = [{"request_id": "r1", "planned_offset_s": "0.5"}, {"request_id": "r2", "planned_offset_s": "1.5"},
                 {"request_id": "r3", "planned_offset_s": "6.0"}]
    dispatcher = [
        {"request_id": "warmup-w1-0", "unfinished_w1": "0", "unfinished_w2": "0", "estimate_w1_ms": "", "estimate_w2_ms": ""},
        {"request_id": "r1", "unfinished_w1": "0", "unfinished_w2": "0", "estimate_w1_ms": "100.000", "estimate_w2_ms": "200.000"},
        {"request_id": "r2", "unfinished_w1": "2", "unfinished_w2": "1", "estimate_w1_ms": "120.000", "estimate_w2_ms": "200.000"},
        {"request_id": "r3", "unfinished_w1": "1", "unfinished_w2": "3", "estimate_w1_ms": "110.000", "estimate_w2_ms": "220.000"},
    ]

    assert pilot.settle_table(dispatcher, generator, bucket_s=5.0) == [
        {"start_s": 0.0, "requests": 2, "unfinished_w1": 1.0, "unfinished_w2": 0.5, "estimate_w1_ms": 110.0, "estimate_w2_ms": 200.0},
        {"start_s": 5.0, "requests": 1, "unfinished_w1": 1.0, "unfinished_w2": 3.0, "estimate_w1_ms": 110.0, "estimate_w2_ms": 220.0},
    ]


def test_the_dry_run_check_names_a_scenario_1_or_2_run_whose_throttling_counters_moved(tmp_path):
    config = load_config(DEV_CONFIG)
    complete_dry_run(tmp_path, config)
    condition = next(c for c in round_conditions(config) if c.scenario == 1)
    run_id = make_run_id(0, condition, 1)
    folder = next(stage_dir(tmp_path, config.stage).glob(f"*/{run_id}"))
    counters = {"nr_periods": 10, "nr_throttled": 0, "throttled_usec": 0}
    moved = {**counters, "nr_throttled": 4, "throttled_usec": 900}
    cpu_stat = {"w1": {"before": counters, "after": counters}, "w2": {"before": counters, "after": moved}}
    (folder / "metadata.json").write_text(json.dumps({"cpu_stat": cpu_stat}), encoding="utf-8")

    assert pilot.check_dry_run(tmp_path, config, 0) == [
        f"{run_id}: w2 was throttled (nr_throttled rose by 4) in scenario 1, which has no quota"]
