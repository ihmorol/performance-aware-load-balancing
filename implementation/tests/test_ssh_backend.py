import csv
import json
from pathlib import Path

import httpx
import pytest

from experiments.backends import BACKENDS
from experiments.orchestrate import Condition, run_condition
from experiments.ssh_backend import SshBackend, parse_cpu_max, parse_cpu_stat
from plb.config import AddressesConfig, Config, MonitoringConfig, QuotaConfig, SshConfig

KEY = str(Path("~/.ssh/plb").expanduser())
W2 = ["ssh", "-i", KEY, "-o", "BatchMode=yes", "plb@10.128.0.22"]
CGROUP = "/sys/fs/cgroup/system.slice/plb-worker.service"


def make_config():
    return Config(
        stage="pilot",
        addresses=AddressesConfig(dispatcher="http://10.128.0.20:8100",
                                  workers=("http://10.128.0.21:8101", "http://10.128.0.22:8102")),
        quota=QuotaConfig(cpu_percent=50.0, period_ms=100),
        monitoring=MonitoringConfig(sampler_interval_s=1.0),
        ssh=SshConfig(user="plb", key_path="~/.ssh/plb"),
    )


class FakeRunner:
    """Records every argv. Replies with the first scripted text whose key is in the command."""

    def __init__(self, replies=None):
        self.calls = []
        self.replies = replies or {}

    def __call__(self, argv):
        self.calls.append(argv)
        command = " ".join(argv)
        return next((text for key, text in self.replies.items() if key in command), "")


def make_backend(replies=None, config_path="config/cloud.toml"):
    runner = FakeRunner(replies)
    return SshBackend(make_config(), Path(config_path), run=runner), runner


def test_ssh_is_registered_next_to_local():
    assert BACKENDS["ssh"] is SshBackend


def test_cpu_stat_text_gives_the_three_counters():
    text = ("usage_usec 81234\nuser_usec 70000\nsystem_usec 11234\n"
            "nr_periods 120\nnr_throttled 37\nthrottled_usec 2500000\n")

    assert parse_cpu_stat(text) == {"nr_periods": 120, "nr_throttled": 37, "throttled_usec": 2500000}


def test_cpu_max_without_a_quota_reads_as_cleared_and_with_one_as_percent_and_period():
    assert parse_cpu_max("max 100000\n") == "cleared"
    assert parse_cpu_max("50000 100000\n") == {"cpu_percent": 50.0, "period_ms": 100}
    assert parse_cpu_max("33300 100000\n") == {"cpu_percent": 33.3, "period_ms": 100}


def test_quota_apply_clear_and_read_back_send_the_exact_commands():
    backend, runner = make_backend({"cpu.max": "50000 100000\n", "cpu.stat": "nr_periods 1\nnr_throttled 0\nthrottled_usec 0\n"})

    backend.apply_quota("w2", 50.0, 100)
    backend.clear_quota("w2")
    quota = backend.verify_quota("w2")
    stat = backend.read_cpu_stat("w2")

    assert runner.calls == [
        W2 + ["sudo -n systemctl set-property --runtime plb-worker.service CPUQuota=50% CPUQuotaPeriodSec=100ms"],
        W2 + ["sudo -n systemctl set-property --runtime plb-worker.service CPUQuota= CPUQuotaPeriodSec="],
        W2 + [f"cat {CGROUP}/cpu.max"],
        W2 + [f"cat {CGROUP}/cpu.stat"],
    ]
    assert quota == {"cpu_percent": 50.0, "period_ms": 100}
    assert stat == {"nr_periods": 1, "nr_throttled": 0, "throttled_usec": 0}


IMPLEMENTATION = Path(__file__).resolve().parents[1]
CONFIG = IMPLEMENTATION / "config" / "cloud.toml"
DISP = ["ssh", "-i", KEY, "-o", "BatchMode=yes", "plb@10.128.0.20"]
W1 = ["ssh", "-i", KEY, "-o", "BatchMode=yes", "plb@10.128.0.21"]
SCP = ["scp", "-i", KEY, "-o", "BatchMode=yes"]


def http_backend(replies=None):
    """An SshBackend whose HTTP requests go to a recording fake."""
    requests = []

    def handler(request):
        requests.append(request)
        if request.url.path == "/admin/cpu":
            return httpx.Response(200, json={"cpu_s": 1.5})
        return httpx.Response(200, json={"status": "ok"})

    runner = FakeRunner(replies)
    backend = SshBackend(make_config(), CONFIG, run=runner, transport=httpx.MockTransport(handler))
    return backend, runner, requests


def test_restart_copies_the_config_and_writes_the_run_parameters_before_systemctl_restart():
    backend, runner, _ = http_backend()

    backend.restart("dispatcher", rule="feedback", scenario=2, rate=2.5, run_id="r1-s2-feedback-2.5-a1")
    backend.restart("w1")

    assert runner.calls == [
        SCP + [str(CONFIG), "plb@10.128.0.20:plb/implementation/config/cloud.toml"],
        DISP + ["printf '%s\\n' PLB_CONFIG=config/cloud.toml PLB_PORT=8100 PLB_RULE=feedback PLB_SCENARIO=2 "
                "PLB_RATE=2.5 PLB_RUN_ID=r1-s2-feedback-2.5-a1 > plb-run/plb-dispatcher.env"
                " && sudo -n systemctl restart plb-dispatcher.service"],
        SCP + [str(CONFIG), "plb@10.128.0.21:plb/implementation/config/cloud.toml"],
        W1 + ["printf '%s\\n' PLB_CONFIG=config/cloud.toml PLB_PORT=8101 > plb-run/plb-worker.env"
              " && sudo -n systemctl restart plb-worker.service"],
    ]


def test_flush_writes_the_log_on_the_vm_and_copies_it_to_the_run_folder(tmp_path):
    backend, runner, requests = http_backend()

    backend.flush("w1", tmp_path / "worker-w1.csv")

    assert [(r.url.path, json.loads(r.content)) for r in requests] == [
        ("/admin/flush", {"path": "/home/plb/plb-run/w1.csv"})]
    assert runner.calls == [SCP + ["plb@10.128.0.21:/home/plb/plb-run/w1.csv", str(tmp_path / "worker-w1.csv")]]


def test_a_service_sampler_runs_on_its_vm_and_its_csv_is_copied_when_it_stops(tmp_path):
    backend, runner, _ = http_backend({"nohup": "4321\n"})

    backend.start_sampler("w1", tmp_path / "sampler-w1.csv")
    backend.stop_sampler("w1")

    assert runner.calls == [
        W1 + ["cd plb/implementation && nohup .venv/bin/python -m experiments.sampler"
              " --out /home/plb/plb-run/sampler-w1.csv --interval 1.0"
              " --pid $(systemctl show -p MainPID --value plb-worker.service) > /dev/null 2>&1 & echo $!"],
        W1 + ["kill 4321"],
        SCP + ["plb@10.128.0.21:/home/plb/plb-run/sampler-w1.csv", str(tmp_path / "sampler-w1.csv")],
    ]


def test_close_stops_the_services_this_backend_started():
    backend, runner, _ = http_backend()
    backend.restart("w1")
    runner.calls.clear()

    backend.close()

    assert runner.calls == [W1 + ["sudo -n systemctl stop plb-worker.service"]]


def test_a_quota_whose_read_back_does_not_match_fails_the_run(tmp_path):
    backend, _, _ = http_backend({**SAME_CPUS, "cpu.max": "max 100000\n"})
    config = make_config()

    assert not run_condition(config, CONFIG, tmp_path, 1, Condition(3, "rr", 1.0), 1, backend)

    rows = list(csv.DictReader(open(tmp_path / "ledger.csv", newline="", encoding="utf-8")))
    assert [row["status"] for row in rows] == ["started", "failed"]
    assert "w2 quota reads cleared" in rows[1]["reason"]


def lscpu(model, cpus=1):
    return f"Architecture:            x86_64\nCPU(s):                  {cpus}\nModel name:              {model}\n"


SAME_CPUS = {"10.128.0.21 lscpu": lscpu("AMD EPYC 7B13"), "10.128.0.22 lscpu": lscpu("AMD EPYC 7B13")}


def test_the_pre_flight_check_passes_when_both_workers_have_the_same_cpu():
    backend, runner, _ = http_backend(SAME_CPUS)

    workers = backend.check_workers()

    assert workers == {"w1": {"cpu_model": "AMD EPYC 7B13", "vcpus": 1},
                       "w2": {"cpu_model": "AMD EPYC 7B13", "vcpus": 1}}
    assert runner.calls == [W1 + ["lscpu"], W2 + ["lscpu"]]


@pytest.mark.parametrize("w2_lscpu", [lscpu("Intel Xeon Platinum 8273CL"), lscpu("AMD EPYC 7B13", cpus=2)])
def test_the_pre_flight_check_fails_when_the_workers_cpu_model_or_count_differ(w2_lscpu):
    backend, _, _ = http_backend({"10.128.0.21 lscpu": lscpu("AMD EPYC 7B13"), "10.128.0.22 lscpu": w2_lscpu})

    with pytest.raises(RuntimeError, match="workers differ"):
        backend.check_workers()
