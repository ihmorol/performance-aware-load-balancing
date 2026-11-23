"""Version record: what machine and software one VM runs, for the paper's setup section.

    python -m experiments.versions --out setup/versions-plb-w1.txt

Run it on each VM. The provider, machine type, and zone come from the
provider's metadata service (Google Cloud, then Azure); "unknown" when none
answers, for example on a laptop.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
from importlib import metadata
from pathlib import Path

import httpx
import psutil

GOOGLE = "http://metadata.google.internal/computeMetadata/v1/instance/"
AZURE = "http://169.254.169.254/metadata/instance?api-version=2021-02-01"
PACKAGES = ("fastapi", "uvicorn", "httpx", "pillow", "psutil", "pytest")


def http_get(url: str, headers: dict) -> str:
    reply = httpx.get(url, headers=headers, timeout=2.0)
    reply.raise_for_status()
    return reply.text


def cloud_details(get) -> dict:
    try:
        headers = {"Metadata-Flavor": "Google"}
        return {"provider": "google",
                "machine_type": get(GOOGLE + "machine-type", headers).rsplit("/", 1)[-1],
                "zone": get(GOOGLE + "zone", headers).rsplit("/", 1)[-1]}
    except Exception:
        pass
    try:
        compute = json.loads(get(AZURE, {"Metadata": "true"}))["compute"]
        zone = compute["location"] + (f"-{compute['zone']}" if compute.get("zone") else "")
        return {"provider": "azure", "machine_type": compute["vmSize"], "zone": zone}
    except Exception:
        return {"provider": "unknown", "machine_type": "unknown", "zone": "unknown"}


def _first_line(command: list[str]) -> str:
    try:
        return subprocess.run(command, capture_output=True, text=True, check=True).stdout.splitlines()[0]
    except (OSError, subprocess.CalledProcessError, IndexError):
        return "unknown"


def _os_release() -> str:
    try:
        fields = dict(line.split("=", 1) for line in Path("/etc/os-release").read_text().splitlines() if "=" in line)
        return fields["PRETTY_NAME"].strip('"')
    except (OSError, KeyError):
        return platform.platform()


def _cpu_model() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "unknown"


def record(get=http_get) -> dict:
    cgroup = "v2" if Path("/sys/fs/cgroup/cgroup.controllers").exists() else "unknown"
    return {
        **cloud_details(get),
        "cpu_model": _cpu_model(),
        "vcpus": os.cpu_count(),
        "ram_mb": psutil.virtual_memory().total // 2**20,
        "os": _os_release(),
        "kernel": platform.release(),
        "systemd": _first_line(["systemctl", "--version"]),
        "cgroup": cgroup,
        "python": platform.python_version(),
        **{name: metadata.version(name) for name in PACKAGES},
    }


def write_record(path: str | Path, get=http_get) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{key}: {value}\n" for key, value in record(get).items()), encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Write this machine's version record.")
    parser.add_argument("--out", required=True, help="text file, for example setup/versions-plb-w1.txt")
    write_record(parser.parse_args(argv).out)


if __name__ == "__main__":
    main()
