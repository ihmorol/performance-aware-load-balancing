"""Backend that runs every service as a process on this machine.

The services are started through their command lines, with the ports from
config.addresses. There are no cgroups here, so the quota and cpu.stat
operations return "unsupported".
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import psutil

from experiments.backends import UNSUPPORTED, Backend
from plb.config import Config

IMPLEMENTATION = Path(__file__).resolve().parents[1]
HEALTH_TIMEOUT_S = 60.0
STOP_TIMEOUT_S = 10.0


class LocalBackend(Backend):
    name = "local"

    def __init__(self, config: Config, config_path: str | Path):
        self.config = config
        self.config_path = Path(config_path).resolve()
        workers = config.addresses.workers
        self.urls = {"w1": workers[0], "w2": workers[1], "dispatcher": config.addresses.dispatcher}
        self.services: dict[str, subprocess.Popen] = {}
        self.samplers: dict[str, subprocess.Popen] = {}
        self.client = httpx.Client(timeout=5.0)

    def start(self, service, rule=None, scenario=None, rate=None, run_id=None):
        module = "dispatcher" if service == "dispatcher" else "worker"
        command = [sys.executable, "-m", module, "--config", str(self.config_path),
                   "--port", str(urlsplit(self.urls[service]).port), "--log", str(self._log_path(service))]
        if service == "dispatcher":
            command += ["--rule", rule, "--scenario", str(scenario), "--rate", str(rate), "--run-id", run_id]
        self.services[service] = subprocess.Popen(command, cwd=IMPLEMENTATION)

    def stop(self, service):
        process = self.services.get(service)
        if process is None:
            return
        if process.poll() is None:
            # On Windows terminate() kills the process at once, so it never
            # writes its shutdown log. Ask for the log first.
            try:
                self.flush(service, self._log_path(service))
            except httpx.HTTPError:
                pass
        _end(process)
        del self.services[service]

    def restart(self, service, rule=None, scenario=None, rate=None, run_id=None):
        self.stop(service)
        self.start(service, rule, scenario, rate, run_id)

    def wait_healthy(self, service):
        deadline = time.monotonic() + HEALTH_TIMEOUT_S
        process = self.services[service]
        while True:
            if process.poll() is not None:
                raise RuntimeError(f"{service} exited with code {process.returncode}")
            try:
                if self.client.get(f"{self.urls[service]}/health").status_code == 200:
                    return
            except httpx.HTTPError:
                pass
            if time.monotonic() > deadline:
                raise TimeoutError(f"{service} was not healthy after {HEALTH_TIMEOUT_S:g} s")
            time.sleep(0.2)

    def apply_quota(self, service, cpu_percent, period_ms):
        return UNSUPPORTED

    def clear_quota(self, service):
        return UNSUPPORTED

    def verify_quota(self, service):
        return UNSUPPORTED

    def read_cpu_stat(self, service):
        return UNSUPPORTED

    def start_sampler(self, name, path):
        command = [sys.executable, "-m", "experiments.sampler", "--out", str(path),
                   "--interval", str(self.config.monitoring.sampler_interval_s)]
        if name != "host":
            command += ["--pid", str(_interpreter_pid(self.services[name]))]
        self.samplers[name] = subprocess.Popen(command, cwd=IMPLEMENTATION)

    def stop_sampler(self, name):
        process = self.samplers.get(name)
        if process is not None:
            _end(process)
            del self.samplers[name]

    def flush(self, service, path):
        reply = self.client.post(f"{self.urls[service]}/admin/flush", json={"path": str(path)})
        reply.raise_for_status()

    def read_dispatcher_cpu(self):
        reply = self.client.get(f"{self.urls['dispatcher']}/admin/cpu")
        reply.raise_for_status()
        return reply.json()["cpu_s"]

    def close(self):
        try:
            for name in list(self.samplers):
                self.stop_sampler(name)
            for service in list(self.services):
                self.stop(service)
        finally:
            # Reached also when an error or Ctrl+C cuts the loops above short.
            for process in [*self.samplers.values(), *self.services.values()]:
                _end(process)
            self.samplers.clear()
            self.services.clear()
            self.client.close()

    def _log_path(self, service: str) -> Path:
        return IMPLEMENTATION / "local" / f"{service}.csv"


def _end(process: subprocess.Popen) -> None:
    try:
        children = psutil.Process(process.pid).children()
    except psutil.NoSuchProcess:
        children = []
    process.terminate()
    try:
        process.wait(timeout=STOP_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    # The interpreter behind a Windows venv launcher (see _interpreter_pid)
    # dies a moment after the launcher. Wait for it, so its port is free.
    _, alive = psutil.wait_procs(children, timeout=STOP_TIMEOUT_S)
    for child in alive:
        child.kill()


def _interpreter_pid(process: subprocess.Popen) -> int:
    # On Windows a venv's python.exe is a launcher that runs the real
    # interpreter as its child, and the service's work happens in that child.
    children = psutil.Process(process.pid).children()
    return children[0].pid if children else process.pid
