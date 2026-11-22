import csv
import json

import pytest

from plb.rows import DISPATCHER_LOG_COLUMNS, GENERATOR_LOG_COLUMNS
from plb.summary import main as summary_main
from plb.summary import nearest_rank, summarize

# A 30 s run whose first 5 s are dropped, so the measured window is 25 s.
RUN = {
    "run_id": "hand", "rule": "rr", "scenario": 2, "rate": 2.0, "round": 1,
    "target": "http://stub/process", "length_s": 30.0, "dropped_window_s": 5.0,
    "achieved_rate_tolerance": 0.05, "schedule_seed": "1:2:2.0:1",
}


def row(planned_s, response_ms=100.0, outcome="success", size_class="medium", actual_s=None, request_id=""):
    """One generator log row, with string values as read from the CSV."""
    actual_s = planned_s if actual_s is None else actual_s
    return {
        "request_id": request_id,
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


def write_csv(path, columns, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, restval="")
        writer.writeheader()
        writer.writerows(rows)


def test_summary_command_writes_summary_json_in_the_run_folder(tmp_path, capsys):
    rows = [row(2.0, 9000), row(6.0, 100, size_class="small"), row(8.0, 300), row(9.0, 50, "rejected")]
    write_csv(tmp_path / "generator.csv", GENERATOR_LOG_COLUMNS, rows)
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
        # No dispatcher.csv or metadata.json in this run folder.
        "mean_select_ns": None, "probe_count": None, "dispatcher_cpu_s": None, "throttling": None,
    }


def dispatcher_row(request_id, select_ns="", probe="0", warmup="0", worker="w1"):
    """One dispatcher log row, with the columns the summary reads."""
    return {"request_id": request_id, "select_ns": select_ns, "probe": probe, "warmup": warmup,
            "chosen_worker": worker}


# r0 is in the dropped window and r3 timed out at the generator.
GENERATOR_ROWS = [
    row(2.0, 100, request_id="r0"), row(6.0, 100, request_id="r1"),
    row(7.0, 300, request_id="r2"), row(8.0, 9000, "timeout", request_id="r3"),
]
DISPATCHER_ROWS = [
    dispatcher_row("warmup-w1-0", warmup="1"), dispatcher_row("warmup-w2-0", warmup="1", worker="w2"),
    dispatcher_row("r0", "100000"),
    dispatcher_row("r1", "2000"), dispatcher_row("probe-w2-0", probe="1", worker="w2"),
    dispatcher_row("r2", "4000", worker="w2"), dispatcher_row("r3", "9000"),
    dispatcher_row("probe-w1-0", probe="1"), dispatcher_row("probe-w2-1", probe="1", worker="w2"),
]


def test_mean_select_time_covers_the_measured_requests_only():
    summary = summarize(GENERATOR_ROWS, RUN, dispatcher_rows=DISPATCHER_ROWS)

    # r1, r2, and r3: (2000 + 4000 + 9000) / 3. r0 is in the dropped window.
    assert summary["mean_select_ns"] == pytest.approx(5000.0)


def test_probe_count_counts_every_probe_row():
    assert summarize(GENERATOR_ROWS, RUN, dispatcher_rows=DISPATCHER_ROWS)["probe_count"] == 3


def test_warm_up_and_probe_rows_stay_out_of_the_response_time_metrics():
    summary = summarize(GENERATOR_ROWS, RUN, dispatcher_rows=DISPATCHER_ROWS)

    # Only r1, r2, and r3 count: two successes at 100 and 300 ms and one timeout.
    assert (summary["measured"], summary["successes"]) == (3, 2)
    assert summary["mean_ms"] == pytest.approx(200.0)
    assert summary["p95_ms"] == pytest.approx(300.0)
    assert summary["throughput"] == pytest.approx(2 / 25)
    assert summary["failures"] == {"rejected": 0, "expired": 0, "timeout": 1, "error": 0}


METADATA = {
    "run_id": "hand", "stage": "pilot", "backend": "local", "quota": "unsupported",
    "cpu_stat": "unsupported", "dispatcher_cpu_s": {"start": 1.25, "end": 4.75},
}


def test_dispatcher_cpu_seconds_are_end_minus_start():
    summary = summarize(GENERATOR_ROWS, RUN, DISPATCHER_ROWS, METADATA)

    assert summary["dispatcher_cpu_s"] == pytest.approx(3.5)


def cpu_stat(nr_periods, nr_throttled, throttled_usec):
    return {"nr_periods": nr_periods, "nr_throttled": nr_throttled, "throttled_usec": throttled_usec}


def test_throttling_is_after_minus_before_for_each_worker_counter():
    metadata = {**METADATA, "cpu_stat": {
        "w1": {"before": cpu_stat(100, 0, 0), "after": cpu_stat(400, 0, 0)},
        "w2": {"before": cpu_stat(120, 5, 2000), "after": cpu_stat(420, 95, 1802000)},
    }}

    summary = summarize(GENERATOR_ROWS, RUN, DISPATCHER_ROWS, metadata)

    assert summary["throttling"] == {
        "w1": {"nr_periods": 300, "nr_throttled": 0, "throttled_usec": 0},
        "w2": {"nr_periods": 300, "nr_throttled": 90, "throttled_usec": 1800000},
    }


def test_throttling_is_none_when_cpu_stat_is_unsupported():
    assert summarize(GENERATOR_ROWS, RUN, DISPATCHER_ROWS, METADATA)["throttling"] is None


@pytest.mark.parametrize("dropped_window_s", [30.0, 31.0])
def test_a_dropped_window_as_long_as_the_run_is_refused(dropped_window_s):
    with pytest.raises(ValueError, match="dropped window"):
        summarize(GENERATOR_ROWS, {**RUN, "dropped_window_s": dropped_window_s})


def test_summary_command_reads_the_dispatcher_log_and_metadata_when_the_run_folder_has_them(tmp_path):
    write_csv(tmp_path / "generator.csv", GENERATOR_LOG_COLUMNS, GENERATOR_ROWS)
    write_csv(tmp_path / "dispatcher.csv", DISPATCHER_LOG_COLUMNS, DISPATCHER_ROWS)
    (tmp_path / "loadgen.json").write_text(json.dumps(RUN), encoding="utf-8")
    (tmp_path / "metadata.json").write_text(json.dumps(METADATA), encoding="utf-8")

    summary_main(["--run-dir", str(tmp_path)])

    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert (summary["mean_select_ns"], summary["probe_count"]) == (5000.0, 3)
    assert summary["dispatcher_cpu_s"] == pytest.approx(3.5)
    assert summary["throttling"] is None
    assert (summary["mean_ms"], summary["p95_ms"]) == (200.0, 300.0)
