import json

import pytest

from experiments.versions import write_record


def google(url, headers):
    assert headers == {"Metadata-Flavor": "Google"}
    if url.endswith("/machine-type"):
        return "projects/123456/machineTypes/t2d-standard-1"
    if url.endswith("/zone"):
        return "projects/123456/zones/us-central1-a"
    raise OSError("not found")


def azure(url, headers):
    if "169.254.169.254" not in url:
        raise OSError("no route")  # the Google name doesn't resolve on Azure
    assert headers == {"Metadata": "true"}
    return json.dumps({"compute": {"vmSize": "Standard_B1s", "location": "eastus", "zone": "1"}})


def no_metadata(url, headers):
    raise OSError("no metadata service")


def read_record(path):
    return dict(line.split(": ", 1) for line in path.read_text(encoding="utf-8").splitlines())


@pytest.mark.parametrize("get, expected", [
    (google, ("google", "t2d-standard-1", "us-central1-a")),
    (azure, ("azure", "Standard_B1s", "eastus-1")),
    (no_metadata, ("unknown", "unknown", "unknown")),
])
def test_the_version_record_names_provider_machine_type_and_zone_from_the_metadata_service(tmp_path, get, expected):
    path = tmp_path / "versions.txt"

    write_record(path, get=get)

    record = read_record(path)
    assert (record["provider"], record["machine_type"], record["zone"]) == expected
    for key in ("cpu_model", "vcpus", "ram_mb", "os", "kernel", "systemd", "cgroup", "python", "pillow", "fastapi"):
        assert record[key]
