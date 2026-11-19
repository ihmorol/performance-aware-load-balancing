import subprocess
from pathlib import Path

import pytest

from plb.config import ConfigError, config_hash, load_config

IMPLEMENTATION = Path(__file__).resolve().parents[1]
DEV_CONFIG = IMPLEMENTATION / "config" / "dev.toml"


def test_dev_config_loads_in_pilot_stage():
    config = load_config(DEV_CONFIG)

    assert config.stage == "pilot"
    assert config.worker.queue_capacity > 0
    assert config.images.resolutions.medium == (1920, 1080)


def full_main_config_text():
    """dev.toml with stage main and the quota keys that dev.toml leaves unset."""
    text = DEV_CONFIG.read_text(encoding="utf-8")
    text = text.replace('stage = "pilot"', 'stage = "main"')
    return text.replace("[quota]\n", "[quota]\ncpu_percent = 50.0\nperiod_ms = 100\n")


def git(repo, *args):
    subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", *args],
        cwd=repo, check=True, capture_output=True,
    )


def committed_repo(tmp_path, config_text):
    git(tmp_path, "init", "-q")
    (tmp_path / "main.toml").write_text(config_text, encoding="utf-8")
    (tmp_path / "code.py").write_text("x = 1\n", encoding="utf-8")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "init")
    return tmp_path / "main.toml"


def test_main_stage_loads_when_every_value_is_set_and_tree_is_clean(tmp_path):
    path = committed_repo(tmp_path, full_main_config_text())

    config = load_config(path)

    assert config.stage == "main"
    assert config.quota.cpu_percent == 50.0


def test_main_stage_with_an_unset_value_raises(tmp_path):
    text = full_main_config_text().replace("ewma_weight = 0.2\n", "")
    path = committed_repo(tmp_path, text)

    with pytest.raises(ConfigError, match="dispatcher.ewma_weight"):
        load_config(path)


def test_main_stage_with_uncommitted_changes_raises(tmp_path):
    path = committed_repo(tmp_path, full_main_config_text())
    (tmp_path / "code.py").write_text("x = 2\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="clean git working tree"):
        load_config(path)


def test_config_hash_changes_when_one_byte_changes(tmp_path):
    path = tmp_path / "a.toml"
    data = bytearray(DEV_CONFIG.read_bytes())
    path.write_bytes(bytes(data))
    before = config_hash(path)

    data[-2] ^= 1
    path.write_bytes(bytes(data))

    assert config_hash(path) != before
