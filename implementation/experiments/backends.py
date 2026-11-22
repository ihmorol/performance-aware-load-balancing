"""Every operation one run needs from the machines, and the list of backends.

The services are "w1", "w2", and "dispatcher". The samplers are "host" and
one per service. An operation a backend can't do returns "unsupported",
which the run records as it is.
"""

from __future__ import annotations

from pathlib import Path

from plb.config import Config

UNSUPPORTED = "unsupported"


class Backend:
    name = ""

    def start(self, service: str, rule=None, scenario=None, rate=None, run_id=None) -> None:
        """Start a service; the dispatcher also gets the run's rule, scenario, rate, and run id."""
        raise NotImplementedError

    def stop(self, service: str) -> None:
        """Stop a service."""
        raise NotImplementedError

    def restart(self, service: str, rule=None, scenario=None, rate=None, run_id=None) -> None:
        """Stop a service if it runs, then start it with the same arguments as start()."""
        raise NotImplementedError

    def wait_healthy(self, service: str) -> None:
        """Return once the service's /health answers 200, or raise."""
        raise NotImplementedError

    def apply_quota(self, service: str, cpu_percent: float, period_ms: int):
        """Put a CPU quota on a worker's service."""
        raise NotImplementedError

    def clear_quota(self, service: str):
        """Remove any CPU quota from a worker's service."""
        raise NotImplementedError

    def verify_quota(self, service: str):
        """Read back the quota: {"cpu_percent": ..., "period_ms": ...}, "cleared", or "unsupported"."""
        raise NotImplementedError

    def read_cpu_stat(self, service: str):
        """nr_periods, nr_throttled, and throttled_usec of a worker's cgroup, or "unsupported"."""
        raise NotImplementedError

    def start_sampler(self, name: str, path: Path) -> None:
        """Start the sampler for "host" or a service; its CSV ends up at path."""
        raise NotImplementedError

    def stop_sampler(self, name: str) -> None:
        """Stop a sampler and make sure its CSV is at the path given to start_sampler()."""
        raise NotImplementedError

    def flush(self, service: str, path: Path) -> None:
        """Have a service write its per-request log, and put the file at path."""
        raise NotImplementedError

    def read_dispatcher_cpu(self) -> float:
        """The dispatcher process's CPU time in seconds."""
        raise NotImplementedError

    def close(self) -> None:
        """Stop every service and sampler this backend started."""
        raise NotImplementedError


# LocalBackend subclasses Backend, so it is imported only after Backend exists.
# Import backends from this module, not from their own modules first.
from experiments.local_backend import LocalBackend  # noqa: E402

BACKENDS = {"local": LocalBackend}


def make_backend(name: str, config: Config, config_path: Path) -> Backend:
    return BACKENDS[name](config, config_path)
