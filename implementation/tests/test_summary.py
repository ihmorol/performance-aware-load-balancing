import csv
import json

import pytest

from plb.rows import GENERATOR_LOG_COLUMNS
from plb.summary import main as summary_main
from plb.summary import nearest_rank, summarize

# A 30 s run whose first 5 s are dropped, so the measured window is 25 s.
RUN = {
    "run_id": "hand", "rule": "rr", "scenario": 2, "rate": 2.0, "round": 1,
    "target": "http://stub/process", "length_s": 30.0, "dropped_window_s": 5.0,
    "achieved_rate_tolerance": 0.05, "schedule_seed": "1:2:2.0:1",
}


def row(planned_s, response_ms=100.0, outcome="success", size_class="medium", actual_s=None):
    """One generator log row, with string values as read from the CSV."""
    actual_s = planned_s if actual_s is None else actual_s
    return {
        "planned_offset_s": f"{planned_s:.6f}",
        "actual_offset_s": f"{actual_s:.6f}",
        "send_lag_ms": f"{(actual_s - planned_s) * 1000:.3f}",
        "size_class": size_class,
        "outcome": outcome,
        "response_ms": f"{response_ms:.3f}",
    }


def test_nearest_rank_p95_of_one_value_is_that_value():
    assert nearest_rank([42.0], 0.95) == 42.0


def test_nearest_rank_p95_of_20_values_is_the_19th_smallest():
    # 1..20 times ten, out of order. ceil(0.95 * 20) = 19, so p95 is 190.
    values = [70, 200, 10, 150, 30, 190, 120, 40, 180, 60, 90, 20, 170, 110, 50, 140, 80, 160, 100, 130]

    assert nearest_rank(values, 0.95) == 190


def test_nearest_rank_p95_of_30_values_rounds_the_rank_up():
    # 0.95 * 30 = 28.5, so p95 is the 29th smallest.
    assert nearest_rank(list(range(30, 0, -1)), 0.95) == 29


def test_nearest_rank_of_no_values_is_none():
    assert nearest_rank([], 0.95) is None


def test_requests_planned_in_the_first_w_seconds_are_left_out():
    rows = [row(1.0, 9000), row(4.999, 9000), row(5.0, 100), row(10.0, 200), row(20.0, 300)]

    summary = summarize(rows, RUN)

    assert summary["measured"] == 3
    assert summary["mean_ms"] == pytest.approx(200.0)
    assert summary["p95_ms"] == pytest.approx(300.0)


def test_mean_and_p95_count_only_successful_requests():
    rows = [row(6.0, 100), row(7.0, 300), row(8.0, 5000, "timeout"), row(9.0, 4000, "rejected")]

    summary = summarize(rows, RUN)

    assert summary["mean_ms"] == pytest.approx(200.0)
    assert summary["p95_ms"] == pytest.approx(300.0)


def test_p95_per_size_class_in_scenario_2():
    rows = [
        row(6.0, 10, size_class="small"), row(7.0, 20, size_class="small"),
        row(8.0, 100, size_class="medium"),
        row(9.0, 1000, size_class="large"), row(10.0, 3000, size_class="large"),
        row(11.0, 2000, size_class="large"), row(12.0, 9000, "timeout", size_class="large"),
        row(1.0, 50, size_class="small"),  # in the dropped window
    ]

    summary = summarize(rows, RUN)

    # small: ceil(0.95 * 2) = 2nd of [10, 20]; large: ceil(0.95 * 3) = 3rd of [1000, 2000, 3000].
    assert summary["p95_by_class_ms"] == {"small": 20.0, "medium": 100.0, "large": 3000.0}


def test_a_class_with_no_successes_has_no_p95():
    rows = [row(6.0, 10, size_class="small"), row(7.0, 900, "rejected", size_class="large")]

    assert summarize(rows, RUN)["p95_by_class_ms"] == {"small": 10.0, "medium": None, "large": None}


def test_scenario_1_has_no_per_class_p95():
    rows = [row(6.0, 100), row(7.0, 200)]

    assert summarize(rows, {**RUN, "scenario": 1})["p95_by_class_ms"] is None


def test_throughput_is_successes_in_the_window_over_its_length():
    successes = [row(5.0 + 0.5 * i) for i in range(50)]  # 50 successes from 5.0 s to 29.5 s
    rejected = [row(6.25 + i, outcome="rejected") for i in range(10)]
    early = [row(1.0 + 0.5 * i) for i in range(5)]  # in the dropped window

    summary = summarize(successes + rejected + early, RUN)

    assert summary["successes"] == 50
    assert summary["throughput"] == pytest.approx(50 / 25)
    assert summary["offered_rate"] == 2.0


def test_failures_are_counted_by_type():
    rows = [
        row(6.0), row(7.0, outcome="rejected"), row(8.0, outcome="rejected"), row(9.0, outcome="rejected"),
        row(10.0, outcome="expired"), row(11.0, outcome="expired"), row(12.0, outcome="timeout"),
        row(2.0, outcome="error"),  # in the dropped window
    ]

    summary = summarize(rows, RUN)

    assert summary["failures"] == {"rejected": 3, "expired": 2, "timeout": 1, "error": 0}


def fifty_planned_with_late_sends(late):
    """50 requests planned from 5.0 s to 29.5 s; the last `late` ones are sent after the run ends."""
    rows = []
    for i in range(50):
        planned = 5.0 + 0.5 * i
        rows.append(row(planned, actual_s=30.2 if i >= 50 - late else planned))
    return rows


def test_rate_flag_is_set_when_the_achieved_rate_misses_the_plan_by_more_than_the_tolerance():
    summary = summarize(fifty_planned_with_late_sends(4), RUN)

    # 46 of 50 sent inside the window: 1.84/s against 2.0/s, an 8 % miss.
    assert summary["planned_rate"] == pytest.approx(2.0)
    assert summary["achieved_rate"] == pytest.approx(1.84)
    assert summary["rate_flag"] is True


def test_rate_flag_is_not_set_inside_the_tolerance():
    summary = summarize(fifty_planned_with_late_sends(2), RUN)

    # 48 of 50: 1.92/s against 2.0/s, a 4 % miss.
    assert summary["achieved_rate"] == pytest.approx(1.92)
    assert summary["rate_flag"] is False


def test_rate_flag_compares_with_the_schedule_not_the_offered_rate():
    # Only 40 requests planned in the window at an offered 2/s: 1.6/s, all sent on time.
    rows = [row(5.0 + 0.5 * i) for i in range(40)]

    summary = summarize(rows, RUN)

    assert summary["planned_rate"] == pytest.approx(1.6)
    assert summary["achieved_rate"] == pytest.approx(1.6)
    assert summary["rate_flag"] is False


def test_max_send_lag_covers_the_measured_window_only():
    rows = [row(6.0, actual_s=6.0), row(7.0, actual_s=7.0125), row(8.0, actual_s=8.003),
            row(1.0, actual_s=1.9)]  # 900 ms late, but in the dropped window

    assert summarize(rows, RUN)["max_send_lag_ms"] == pytest.approx(12.5)


def test_summary_command_writes_summary_json_in_the_run_folder(tmp_path, capsys):
    rows = [row(2.0, 9000), row(6.0, 100, size_class="small"), row(8.0, 300), row(9.0, 50, "rejected")]
    with open(tmp_path / "generator.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=GENERATOR_LOG_COLUMNS, restval="")
        writer.writeheader()
        writer.writerows(rows)
    (tmp_path / "loadgen.json").write_text(json.dumps(RUN), encoding="utf-8")

    summary_main(["--run-dir", str(tmp_path)])

    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert str(tmp_path / "summary.json") in capsys.readouterr().out
    assert summary == {
        "run_id": "hand", "rule": "rr", "scenario": 2, "round": 1,
        "measured": 3, "successes": 2, "mean_ms": 200.0, "p95_ms": 300.0,
        "p95_by_class_ms": {"small": 100.0, "medium": 300.0, "large": None},
        "throughput": 0.08, "offered_rate": 2.0,
        "failures": {"rejected": 1, "expired": 0, "timeout": 0, "error": 0},
        "planned_rate": 0.12, "achieved_rate": 0.12, "rate_flag": False, "max_send_lag_ms": 0.0,
    }
