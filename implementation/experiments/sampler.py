"""Resource sampler: one CSV row per interval.

    python -m experiments.sampler --out local/sampler-host.csv --interval 1 --pid 1234

Each row holds the wall-clock time, total CPU, CPU of the --pid process, and
RAM used. Without --pid the process column is empty. The sampler runs until
it is killed, or stops by itself when the --pid process ends.
"""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

import psutil

COLUMNS = ("timestamp_unix_s", "cpu_total_percent", "cpu_process_percent", "ram_used_mb")


def take_sample(process: psutil.Process | None) -> dict:
    """One row. Both CPU values cover the time since the previous call.

    The process value is a percent of one CPU, as psutil gives it.
    """
    return {
        "timestamp_unix_s": f"{time.time():.3f}",
        "cpu_total_percent": psutil.cpu_percent(),
        "cpu_process_percent": "" if process is None else process.cpu_percent(),
        "ram_used_mb": f"{psutil.virtual_memory().used / 2**20:.1f}",
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Write one resource sample per interval to a CSV file.")
    parser.add_argument("--out", required=True, help="CSV file")
    parser.add_argument("--interval", type=float, required=True, help="seconds between rows")
    parser.add_argument("--pid", type=int, help="process whose CPU goes in cpu_process_percent")
    args = parser.parse_args(argv)

    process = None
    if args.pid is not None:
        try:
            process = psutil.Process(args.pid)
        except psutil.NoSuchProcess:
            parser.error(f"no process with pid {args.pid}")
    take_sample(process)  # starts both CPU counters; its values cover no time yet

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        while True:
            time.sleep(args.interval)
            try:
                row = take_sample(process)
            except psutil.NoSuchProcess:
                return  # the watched process has ended
            writer.writerow(row)
            # Flushed every row, so a hard kill loses at most the row being written.
            f.flush()


if __name__ == "__main__":
    main()
