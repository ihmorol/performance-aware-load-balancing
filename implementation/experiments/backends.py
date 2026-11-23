"""The backends the orchestrator can run on, by name."""

from __future__ import annotations

from pathlib import Path

from experiments.backend import Backend
from experiments.local_backend import LocalBackend
from experiments.ssh_backend import SshBackend
from plb.config import Config

BACKENDS = {"local": LocalBackend, "ssh": SshBackend}


def make_backend(name: str, config: Config, config_path: Path) -> Backend:
    return BACKENDS[name](config, config_path)
