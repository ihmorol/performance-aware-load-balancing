"""Load and check the one TOML config file that holds every tunable value.

The schema below is the whole key list from the "Config" section of
implementation/spec.md, plus the SSH login that issue #6 needs and the
largest weight sum that issue #7's calibration rounds to. A key that is missing from the file loads as None.
That is allowed in the pilot stage, where the pilot has not decided every
value yet. In the main stage every key must be set and the git working tree
must be clean, or loading raises ConfigError.
"""

from __future__ import annotations

import dataclasses
import hashlib
import subprocess
import tomllib
import types
import typing
from dataclasses import dataclass
from pathlib import Path

STAGES = ("pilot", "main")


class ConfigError(Exception):
    """The config file is malformed, or not ready for the stage it names."""


@dataclass(frozen=True)
class AddressesConfig:
    # Base URLs such as "http://127.0.0.1:8100".
    dispatcher: str | None = None
    workers: tuple[str, ...] | None = None


@dataclass(frozen=True)
class WorkerConfig:
    # Requests that may wait behind the one being processed.
    queue_capacity: int | None = None


@dataclass(frozen=True)
class DispatcherConfig:
    # Dispatcher timeout D, also sent to the worker as the time budget.
    timeout_ms: int | None = None
    # Weight a in estimate = (1 - a) * estimate + a * newest time.
    ewma_weight: float | None = None
    # Probe threshold T: seconds without a completion before a probe.
    probe_threshold_s: float | None = None
    # Warm-up count K: requests sent to each worker before a run.
    warmup_count: int | None = None


@dataclass(frozen=True)
class GeneratorConfig:
    # Generator timeout, D plus a fixed margin.
    timeout_ms: int | None = None
    # Busy-wait just before each planned send time.
    spin_wait: bool | None = None


@dataclass(frozen=True)
class RunConfig:
    length_s: float | None = None
    # Dropped window W: requests planned in the first W seconds are left out.
    dropped_window_s: float | None = None
    # Largest allowed relative miss of the planned rate, such as 0.05.
    achieved_rate_tolerance: float | None = None


@dataclass(frozen=True)
class RatesConfig:
    # Three request rates per scenario, in requests per second.
    scenario1: tuple[float, float, float] | None = None
    scenario2: tuple[float, float, float] | None = None
    scenario3: tuple[float, float, float] | None = None


@dataclass(frozen=True)
class WeightsConfig:
    # Largest allowed sum of the two weights when calibration rounds
    # throughputs to a small integer ratio.
    max_sum: int | None = None
    # Smooth weighted round-robin weights for worker 1 and worker 2.
    scenario1: tuple[int, int] | None = None
    scenario2: tuple[int, int] | None = None
    scenario3: tuple[int, int] | None = None


@dataclass(frozen=True)
class ResolutionsConfig:
    # Width and height in pixels for each size class.
    small: tuple[int, int] | None = None
    medium: tuple[int, int] | None = None
    large: tuple[int, int] | None = None


@dataclass(frozen=True)
class MixConfig:
    # Share of each size class in scenarios 2 and 3.
    small: float | None = None
    medium: float | None = None
    large: float | None = None


@dataclass(frozen=True)
class ImagesConfig:
    per_class: int | None = None
    resolutions: ResolutionsConfig = ResolutionsConfig()
    mix: MixConfig = MixConfig()


@dataclass(frozen=True)
class QuotaConfig:
    # CPU quota on the slowed worker in scenario 3 (systemd CPUQuota=).
    cpu_percent: float | None = None
    # Quota period (systemd CPUQuotaPeriodSec=).
    period_ms: int | None = None


@dataclass(frozen=True)
class MonitoringConfig:
    sampler_interval_s: float | None = None
    # CPU percent the generator host and dispatcher must stay below.
    bottleneck_cpu_percent: float | None = None


@dataclass(frozen=True)
class SeedsConfig:
    image_set: int | None = None
    # Base seed; the schedule seed also depends on scenario, rate, and round.
    schedule: int | None = None
    round_order: int | None = None


@dataclass(frozen=True)
class SshConfig:
    # Login and private key the orchestrator uses for ssh and scp to the VMs.
    # The VM hosts come from the addresses section.
    user: str | None = None
    key_path: str | None = None


@dataclass(frozen=True)
class Config:
    stage: str
    addresses: AddressesConfig = AddressesConfig()
    worker: WorkerConfig = WorkerConfig()
    dispatcher: DispatcherConfig = DispatcherConfig()
    generator: GeneratorConfig = GeneratorConfig()
    run: RunConfig = RunConfig()
    rates: RatesConfig = RatesConfig()
    weights: WeightsConfig = WeightsConfig()
    images: ImagesConfig = ImagesConfig()
    quota: QuotaConfig = QuotaConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    seeds: SeedsConfig = SeedsConfig()
    ssh: SshConfig = SshConfig()


def load_config(path: str | Path) -> Config:
    """Read a config file and check it against the schema and its stage."""
    path = Path(path)
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path}: {exc}") from exc

    stage = raw.pop("stage", None)
    if stage not in STAGES:
        raise ConfigError(f"{path}: stage must be one of {STAGES}, got {stage!r}")

    sections = _build(Config, raw, prefix="", skip={"stage"})
    config = Config(stage=stage, **sections)

    if stage == "main":
        unset = _unset_keys(config)
        if unset:
            raise ConfigError(f"{path}: main stage needs every value set; unset: {', '.join(unset)}")
        _require_clean_git(path.parent)
    return config


def config_hash(path: str | Path) -> str:
    """SHA-256 of the config file's bytes, as hex."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git_commit(directory: str | Path = ".") -> str:
    """Commit id of HEAD in the git repository that holds `directory`."""
    return _git(directory, "rev-parse", "HEAD").strip()


def _require_clean_git(directory: Path) -> None:
    # Untracked files are ignored: run outputs land in the tree during a
    # round, and code only takes effect once tracked code imports it.
    status = _git(directory, "status", "--porcelain", "--untracked-files=no")
    if status.strip():
        raise ConfigError(f"main stage needs a clean git working tree; uncommitted changes:\n{status}")


def _git(directory: str | Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args], cwd=directory, capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise ConfigError(f"git {' '.join(args)} failed in {directory}: {detail}") from exc
    return result.stdout


def _build(cls: type, table: dict, prefix: str, skip: frozenset | set = frozenset()) -> dict:
    hints = typing.get_type_hints(cls)
    names = {f.name for f in dataclasses.fields(cls)} - set(skip)
    unknown = set(table) - names
    if unknown:
        raise ConfigError(f"unknown config key(s): {', '.join(prefix + k for k in sorted(unknown))}")

    values = {}
    for name in names:
        hint = hints[name]
        key = prefix + name
        if dataclasses.is_dataclass(hint):
            sub = table.get(name, {})
            if not isinstance(sub, dict):
                raise ConfigError(f"{key} must be a table")
            values[name] = hint(**_build(hint, sub, prefix=key + "."))
        elif name in table:
            values[name] = _check_value(key, table[name], hint)
    return values


def _check_value(key: str, value: object, hint: object) -> object:
    # Every leaf is `X | None`; find X.
    (base,) = [a for a in typing.get_args(hint) if a is not types.NoneType]
    if typing.get_origin(base) is tuple:
        args = typing.get_args(base)
        if not isinstance(value, list):
            raise ConfigError(f"{key} must be a list")
        if args[-1] is Ellipsis:
            element_types = [args[0]] * len(value)
        else:
            element_types = list(args)
            if len(value) != len(element_types):
                raise ConfigError(f"{key} must have {len(element_types)} items")
        return tuple(_check_scalar(key, v, t) for v, t in zip(value, element_types))
    return _check_scalar(key, value, base)


def _check_scalar(key: str, value: object, expected: type) -> object:
    # bool is a subclass of int in Python, so rule it out by hand.
    if expected is not bool and isinstance(value, bool):
        raise ConfigError(f"{key} must be {expected.__name__}, got a boolean")
    if expected is float and isinstance(value, int):
        return float(value)
    if not isinstance(value, expected):
        raise ConfigError(f"{key} must be {expected.__name__}, got {type(value).__name__}")
    return value


def _unset_keys(section: object, prefix: str = "") -> list[str]:
    unset = []
    for f in dataclasses.fields(section):
        value = getattr(section, f.name)
        if dataclasses.is_dataclass(value):
            unset += _unset_keys(value, prefix + f.name + ".")
        elif value is None:
            unset.append(prefix + f.name)
    return unset
