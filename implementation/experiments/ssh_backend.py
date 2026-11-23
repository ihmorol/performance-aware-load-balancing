"""Backend that runs the services on Linux VMs, reached with ssh and scp.

Works on any provider: it uses only the addresses and the [ssh] section of
the config. Each VM runs the systemd units from implementation/setup/ under
the user "plb", with the code cloned at ~/plb. Setup is in
implementation/setup/README.md.
"""

from __future__ import annotations

import shlex
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from experiments.backend import Backend
from experiments.local_backend import HEALTH_TIMEOUT_S, IMPLEMENTATION, _end, is_healthy
from plb.config import Config

UNITS = {"w1": "plb-worker.service", "w2": "plb-worker.service", "dispatcher": "plb-dispatcher.service"}
# On each VM, relative to the user's home: run files (env files, logs, sampler CSVs).
RUN_DIR = "plb-run"


def run_command(argv: list[str]) -> str:
    """Run one ssh or scp command and return its output. Every call goes through here."""
    result = subprocess.run(argv, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(argv)} failed with code {result.returncode}: {result.stderr.strip()}")
    return result.stdout


def parse_cpu_stat(text: str) -> dict:
    """The three throttling counters from a cgroup v2 cpu.stat file."""
    values = dict(line.split() for line in text.splitlines() if line.strip())
    return {key: int(values[key]) for key in ("nr_periods", "nr_throttled", "throttled_usec")}


def parse_cpu_max(text: str):
    """cgroup v2 cpu.max: "max <period>" is no quota, "<quota> <period>" a quota, both in microseconds."""
    quota, period = text.split()
    if quota == "max":
        return "cleared"
    return {"cpu_percent": round(int(quota) * 100 / int(period), 3), "period_ms": int(period) // 1000}


class SshBackend(Backend):
    name = "ssh"

    def __init__(self, config: Config, config_path: str | Path, run=run_command, transport=None):
        self.config = config
        self.config_path = Path(config_path).resolve()
        self.run = run
        workers = config.addresses.workers
        self.urls = {"w1": workers[0], "w2": workers[1], "dispatcher": config.addresses.dispatcher}
        self.key = str(Path(config.ssh.key_path).expanduser())
        self.home = f"/home/{config.ssh.user}"
        # Health, flush, and CPU time go straight to the services over the private network.
        self.client = httpx.Client(timeout=5.0, transport=transport)
        self.started: list[str] = []
        self.samplers: dict[str, tuple[str, str, Path]] = {}  # name: (pid, file on the VM, file here)
        self.host_sampler: subprocess.Popen | None = None

    def _target(self, service: str) -> str:
        return f"{self.config.ssh.user}@{urlsplit(self.urls[service]).hostname}"

    def _ssh(self, service: str, command: str) -> str:
        return self.run(["ssh", "-i", self.key, "-o", "BatchMode=yes", self._target(service), command])

    def _scp(self, source: str, destination: str) -> None:
        self.run(["scp", "-i", self.key, "-o", "BatchMode=yes", source, destination])

    def start(self, service, rule=None, scenario=None, rate=None, run_id=None):
        # systemctl restart also starts a stopped unit.
        self.restart(service, rule, scenario, rate, run_id)

    def stop(self, service):
        self._ssh(service, f"sudo -n systemctl stop {UNITS[service]}")

    def restart(self, service, rule=None, scenario=None, rate=None, run_id=None):
        # The clone on the VM has the same layout, so the config goes to the same place in it.
        config = self.config_path.relative_to(IMPLEMENTATION).as_posix()
        self._scp(str(self.config_path), f"{self._target(service)}:plb/implementation/{config}")
        # The unit reads its arguments from this file, so sudo only needs a plain restart.
        env = {"PLB_CONFIG": config, "PLB_PORT": urlsplit(self.urls[service]).port}
        if service == "dispatcher":
            env |= {"PLB_RULE": rule, "PLB_SCENARIO": scenario, "PLB_RATE": rate, "PLB_RUN_ID": run_id}
        lines = " ".join(shlex.quote(f"{key}={value}") for key, value in env.items())
        unit = UNITS[service]
        self._ssh(service, f"printf '%s\\n' {lines} > {RUN_DIR}/{unit.removesuffix('.service')}.env"
                           f" && sudo -n systemctl restart {unit}")
        if service not in self.started:
            self.started.append(service)

    def wait_healthy(self, service):
        deadline = time.monotonic() + HEALTH_TIMEOUT_S
        while True:
            try:
                if is_healthy(service, self.client.get(f"{self.urls[service]}/health")):
                    return
            except httpx.HTTPError:
                pass
            if time.monotonic() > deadline:
                raise TimeoutError(f"{service} was not healthy after {HEALTH_TIMEOUT_S:g} s")
            time.sleep(0.5)

    def start_sampler(self, name, path):
        interval = self.config.monitoring.sampler_interval_s
        if name == "host":
            # The orchestrator runs on the generator VM, which is "the host".
            self.host_sampler = subprocess.Popen(
                [sys.executable, "-m", "experiments.sampler", "--out", str(path), "--interval", str(interval)],
                cwd=IMPLEMENTATION)
            return
        remote = f"{self.home}/{RUN_DIR}/sampler-{name}.csv"
        pid = self._ssh(name, f"cd plb/implementation && nohup .venv/bin/python -m experiments.sampler"
                              f" --out {remote} --interval {interval}"
                              f" --pid $(systemctl show -p MainPID --value {UNITS[name]}) > /dev/null 2>&1 & echo $!")
        self.samplers[name] = (pid.strip(), remote, Path(path))

    def stop_sampler(self, name):
        if name == "host":
            if self.host_sampler is not None:
                _end(self.host_sampler)
                self.host_sampler = None
            return
        pid, remote, path = self.samplers.pop(name)
        self._ssh(name, f"kill {pid}")
        self._scp(f"{self._target(name)}:{remote}", str(path))

    def flush(self, service, path):
        remote = f"{self.home}/{RUN_DIR}/{service}.csv"
        self.client.post(f"{self.urls[service]}/admin/flush", json={"path": remote}).raise_for_status()
        self._scp(f"{self._target(service)}:{remote}", str(path))

    def read_dispatcher_cpu(self):
        reply = self.client.get(f"{self.urls['dispatcher']}/admin/cpu")
        reply.raise_for_status()
        return reply.json()["cpu_s"]

    def close(self):
        """Stop what this backend started. Each step is tried, so one failure leaves nothing else running."""
        commands = [(name, f"kill {pid}") for name, (pid, _, _) in self.samplers.items()]
        commands += [(service, f"sudo -n systemctl stop {UNITS[service]}") for service in self.started]
        try:
            for service, command in commands:
                try:
                    self._ssh(service, command)
                except RuntimeError:
                    pass
        finally:
            if self.host_sampler is not None:
                _end(self.host_sampler)
            self.samplers.clear()
            self.started.clear()
            self.host_sampler = None
            self.client.close()

    def _cgroup_file(self, service: str, name: str) -> str:
        return self._ssh(service, f"cat /sys/fs/cgroup/system.slice/{UNITS[service]}/{name}")

    def check_workers(self):
        cpus = {}
        for worker in ("w1", "w2"):
            fields = dict(line.split(":", 1) for line in self._ssh(worker, "lscpu").splitlines() if ":" in line)
            cpus[worker] = {"cpu_model": fields["Model name"].strip(), "vcpus": int(fields["CPU(s)"])}
        if cpus["w1"] != cpus["w2"]:
            raise RuntimeError(f"the workers differ, so the comparison would not be fair: {cpus}")
        return cpus

    def apply_quota(self, service, cpu_percent, period_ms):
        self._ssh(service, f"sudo -n systemctl set-property --runtime {UNITS[service]} "
                           f"CPUQuota={cpu_percent:g}% CPUQuotaPeriodSec={period_ms}ms")

    def clear_quota(self, service):
        # An empty value resets a property: no quota, the default period.
        self._ssh(service, f"sudo -n systemctl set-property --runtime {UNITS[service]} CPUQuota= CPUQuotaPeriodSec=")

    def verify_quota(self, service):
        return parse_cpu_max(self._cgroup_file(service, "cpu.max"))

    def read_cpu_stat(self, service):
        return parse_cpu_stat(self._cgroup_file(service, "cpu.stat"))
