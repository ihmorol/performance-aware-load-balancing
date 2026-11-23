import fnmatch
import re
from pathlib import Path

import pytest

from experiments.ssh_backend import UNITS
from plb.config import load_config

SETUP = Path(__file__).resolve().parents[1] / "setup"
VENV_PYTHON = "/home/plb/plb/implementation/.venv/bin/python"


@pytest.mark.parametrize("unit, module", [("plb-worker.service", "worker"), ("plb-dispatcher.service", "dispatcher")])
def test_a_unit_file_has_no_cpu_quota_and_runs_one_service_process_from_the_venv(unit, module):
    text = (SETUP / unit).read_text(encoding="utf-8")
    exec_lines = [line for line in text.splitlines() if line.startswith("ExecStart=")]

    assert "CPUQuota" not in text
    assert exec_lines == [f"ExecStart={VENV_PYTHON} -m {module} " + exec_lines[0].split(f"-m {module} ", 1)[1]]
    assert "Type=simple" in text


def sudoers_commands():
    text = (SETUP / "plb-sudoers").read_text(encoding="utf-8").replace("\\\n", " ")
    rules = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    assert len(rules) == 1 and rules[0].startswith("plb ALL=(root) NOPASSWD: ")
    return [command.strip() for command in rules[0].split("NOPASSWD: ", 1)[1].split(",")]


def test_the_sudo_rule_allows_only_systemctl_for_the_two_services():
    for command in sudoers_commands():
        assert re.fullmatch(r"/usr/bin/systemctl (restart|stop|set-property --runtime) "
                            r"(plb-worker|plb-dispatcher)\.service( \*)?", command), command


@pytest.mark.parametrize("command", [
    f"systemctl restart {UNITS['w1']}", f"systemctl stop {UNITS['w1']}",
    f"systemctl restart {UNITS['dispatcher']}", f"systemctl stop {UNITS['dispatcher']}",
    "systemctl set-property --runtime plb-worker.service CPUQuota=50% CPUQuotaPeriodSec=100ms",
    "systemctl set-property --runtime plb-worker.service CPUQuota= CPUQuotaPeriodSec=",
])
def test_every_sudo_command_the_ssh_backend_sends_is_allowed(command):
    assert any(fnmatch.fnmatchcase("/usr/bin/" + command, allowed) for allowed in sudoers_commands())


def test_the_setup_guide_covers_both_providers_and_every_step_without_virtualbox():
    text = (SETUP / "README.md").read_text(encoding="utf-8")
    headings = [line[3:].lower() for line in text.splitlines() if line.startswith("## ")]

    for part in ("google cloud", "azure for students", "network", "vm install", "ssh keys", "sudo rule",
                 "services", "background jobs disabled", "version record", "reset"):
        assert any(part in heading for heading in headings), part
    assert "virtualbox" not in text.lower()
    assert "payment card" in text.lower()


def test_the_cloud_config_loads_and_points_at_the_four_vms():
    config = load_config(SETUP.parent / "config" / "cloud.toml")

    assert config.addresses.dispatcher == "http://10.128.0.20:8100"
    assert config.addresses.workers == ("http://10.128.0.21:8101", "http://10.128.0.22:8102")
    assert (config.ssh.user, config.ssh.key_path) == ("plb", "~/.ssh/plb")
