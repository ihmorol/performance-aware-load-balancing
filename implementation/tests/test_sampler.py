import csv
import subprocess
import sys
import time
from pathlib import Path

import psutil

from experiments.sampler import take_sample

COLUMNS = ["timestamp_unix_s", "cpu_total_percent", "cpu_process_percent", "ram_used_mb"]
IMPLEMENTATION = Path(__file__).resolve().parents[1]


def start_sampler(out, *args):
    return subprocess.Popen(
        [sys.executable, "-m", "experiments.sampler", "--out", str(out), "--interval", "0.1", *args],
        cwd=IMPLEMENTATION,
    )


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def busy(seconds):
    end = time.perf_counter() + seconds
    while time.perf_counter() < end:
        pass


def test_one_sample_has_the_four_columns_with_plausible_values():
    process = psutil.Process()  # this test's own process
    take_sample(process)  # psutil counts CPU from the previous call, so the first one only starts it
    busy(0.3)

    sample = take_sample(process)

    assert list(sample) == COLUMNS
    assert abs(float(sample["timestamp_unix_s"]) - time.time()) < 5
    assert 0 <= float(sample["cpu_total_percent"]) <= 100
    # The process was busy the whole time, so it used about one full CPU. Windows
    # counts process CPU time in steps of about 15.6 ms, so it can read a bit over 100.
    assert 50 < float(sample["cpu_process_percent"]) < 120
    assert float(sample["ram_used_mb"]) > 0


def test_without_a_process_the_process_column_is_empty():
    sample = take_sample(None)

    assert sample["cpu_process_percent"] == ""
    assert float(sample["ram_used_mb"]) > 0


def test_sampler_stops_by_itself_when_the_watched_process_ends(tmp_path):
    out = tmp_path / "sampler.csv"
    watched = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(1)"])
    sampler = start_sampler(out, "--pid", str(watched.pid))
    try:
        watched.wait(timeout=10)
        code = sampler.wait(timeout=10)
    finally:
        watched.kill()
        sampler.kill()

    header, *rows = read_csv(out)
    assert code == 0
    assert header == COLUMNS
    # About ten rows at 0.1 s over the watched process's 1 s.
    assert len(rows) >= 3
    assert all(row[2] != "" for row in rows)


def test_rows_reach_the_file_while_the_sampler_runs(tmp_path):
    out = tmp_path / "sampler.csv"
    sampler = start_sampler(out)
    try:
        deadline = time.monotonic() + 10
        while not (out.exists() and len(read_csv(out)) >= 4):
            assert time.monotonic() < deadline, "no rows reached the file"
            assert sampler.poll() is None, "the sampler stopped by itself"
            time.sleep(0.05)
        header, *rows = read_csv(out)  # read before the sampler is stopped
    finally:
        sampler.terminate()  # a hard kill on Windows
        sampler.wait(timeout=10)

    assert header == COLUMNS
    assert len(rows) >= 3
    assert all(row[2] == "" for row in rows)
