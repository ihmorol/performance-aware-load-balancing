"""Per-run summary of response times, from the generator log only.

The rules follow "Per-run summary" in implementation/spec.md. The summary
reads generator.csv and loadgen.json from the run folder and writes
summary.json next to them.

    python -m plb.summary --run-dir local/run-manual
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from plb import protocol
from plb.images import SIZE_CLASSES

FAILURES = (protocol.REJECTED, protocol.EXPIRED, protocol.TIMEOUT, protocol.ERROR)


def nearest_rank(values: list[float], q: float) -> float | None:
    """The value at position ceil(q * n) after sorting, counting from 1."""
    if not values:
        return None
    return sorted(values)[math.ceil(q * len(values)) - 1]


def summarize(rows: list[dict], run: dict) -> dict:
    """Summarize one run's generator log rows. run holds the loadgen.json values."""
    window_start = run["dropped_window_s"]
    length_s = run["length_s"]
    window_s = length_s - window_start
    measured = [r for r in rows if float(r["planned_offset_s"]) >= window_start]
    successes = [r for r in measured if r["outcome"] == protocol.SUCCESS]
    times = [float(r["response_ms"]) for r in successes]

    by_class = None
    # Scenario 1 uses only the medium class, so a per-class p95 says nothing new.
    if run["scenario"] != 1:
        by_class = {
            size_class: nearest_rank([float(r["response_ms"]) for r in successes
                                      if r["size_class"] == size_class], 0.95)
            for size_class in SIZE_CLASSES
        }

    # The flag compares with what the schedule planned for the window, not with the
    # offered rate, so Poisson noise never sets it. An empty window is flagged too.
    planned_rate = len(measured) / window_s
    achieved_rate = sum(window_start <= float(r["actual_offset_s"]) < length_s for r in rows) / window_s
    rate_flag = (planned_rate == 0
                 or abs(achieved_rate - planned_rate) / planned_rate > run["achieved_rate_tolerance"])
    lags = [float(r["send_lag_ms"]) for r in measured]

    return {
        "run_id": run["run_id"],
        "rule": run["rule"],
        "scenario": run["scenario"],
        "round": run["round"],
        "measured": len(measured),
        "successes": len(successes),
        "mean_ms": sum(times) / len(times) if times else None,
        "p95_ms": nearest_rank(times, 0.95),
        "p95_by_class_ms": by_class,
        "throughput": len(successes) / window_s,
        "offered_rate": run["rate"],
        "failures": {outcome: sum(r["outcome"] == outcome for r in measured) for outcome in FAILURES},
        "planned_rate": planned_rate,
        "achieved_rate": achieved_rate,
        "rate_flag": rate_flag,
        "max_send_lag_ms": max(lags) if lags else None,
    }


def summarize_run_dir(run_dir: str | Path) -> Path:
    """Write summary.json in run_dir and return its path."""
    run_dir = Path(run_dir)
    with open(run_dir / "generator.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    run = json.loads((run_dir / "loadgen.json").read_text(encoding="utf-8"))
    path = run_dir / "summary.json"
    path.write_text(json.dumps(summarize(rows, run), indent=2) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Summarize one run's generator log.")
    parser.add_argument("--run-dir", required=True, help="run folder with generator.csv and loadgen.json")
    args = parser.parse_args(argv)
    print(summarize_run_dir(args.run_dir))


if __name__ == "__main__":
    main()
