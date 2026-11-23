import asyncio
import csv
import json
import socket
import threading
import time
from contextlib import contextmanager

import anyio
import pytest
import uvicorn
from fastapi import FastAPI, Request, Response

from experiments.loadgen import main as loadgen_main
from experiments.loadgen import send_schedule
from experiments.schedule import PlannedRequest
from plb.rows import GENERATOR_LOG_COLUMNS
from test_config import committed_repo, full_main_config_text


def stub_app(delay_s, status=200, headers=None):
    """A target that waits delay_s before each reply.

    It runs in the test's process, so its perf_counter times compare with the sender's.
    """
    app = FastAPI()
    app.state.request_headers = []
    app.state.arrived_at = []
    app.state.replied_at = []

    @app.post("/process")
    async def process(request: Request) -> Response:
        app.state.arrived_at.append(time.perf_counter())
        app.state.request_headers.append(dict(request.headers))
        await request.body()
        await asyncio.sleep(delay_s)
        app.state.replied_at.append(time.perf_counter())
        return Response(content=b"output", status_code=status, headers=headers)

    return app


@contextmanager
def serving(app):
    """Run app on a real Uvicorn server on a free local port, in a thread."""
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    # Requests still sleeping in the stub are cut off one second after the test.
    config = uvicorn.Config(app, log_level="warning", timeout_graceful_shutdown=1)
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]})
    thread.start()
    try:
        deadline = time.monotonic() + 5
        while not server.started:
            assert time.monotonic() < deadline, "stub server did not start"
            time.sleep(0.01)
        yield f"http://127.0.0.1:{port}/process"
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        sock.close()


def hand_schedule(*offsets, image_id="medium-00"):
    """A schedule with exactly these planned offsets, in seconds."""
    size_class = image_id.split("-")[0]
    return [PlannedRequest(f"r{i:05d}", offset, image_id, size_class) for i, offset in enumerate(offsets)]


BODIES = {"medium-00": b"medium image bytes", "small-01": b"small image bytes"}


def send(url, schedule, timeout_s=10.0, spin_wait=False):
    return send_schedule(url, "test-run", schedule, BODIES, timeout_s, spin_wait)


@pytest.mark.anyio
async def test_every_request_in_the_first_2_s_is_sent_before_the_first_reply():
    app = stub_app(delay_s=2.0)
    with serving(app) as url:
        with anyio.fail_after(10):
            rows = await send(url, hand_schedule(0.0, 0.5, 1.0, 1.5))

    assert [r["outcome"] for r in rows] == ["success"] * 4
    # Arrival at the stub, not the send stamp, so a sender waiting for a free
    # connection would fail here.
    assert len(app.state.arrived_at) == 4
    assert max(app.state.arrived_at) < min(app.state.replied_at)


async def block_event_loop(after_s, for_s):
    await asyncio.sleep(after_s)
    time.sleep(for_s)  # no task can run, so a send due now goes out late


@pytest.mark.anyio
async def test_response_time_counts_from_the_planned_send_time():
    with serving(stub_app(delay_s=0.3)) as url:
        with anyio.fail_after(10):
            # The request is planned at 0.1 s, but the loop is blocked from
            # about 0.05 s to 0.55 s, so it is sent about 0.45 s late.
            rows, _ = await asyncio.gather(send(url, hand_schedule(0.1)), block_event_loop(0.05, 0.5))

    (row,) = rows
    send_lag_ms, response_ms = float(row["send_lag_ms"]), float(row["response_ms"])
    assert row["outcome"] == "success"
    assert send_lag_ms > 350
    # Planned-based: the lag plus the stub's 300 ms, not the 300 ms alone.
    assert response_ms > 300 + 350
    assert abs(response_ms - (send_lag_ms + 300)) < 200


@pytest.mark.anyio
async def test_with_spin_wait_requests_go_out_on_time_and_never_early():
    offsets = [0.013 + 0.047 * i for i in range(12)]
    with serving(stub_app(delay_s=0)) as url:
        with anyio.fail_after(5):
            rows = await send(url, hand_schedule(*offsets), spin_wait=True)

    lags = sorted(float(r["send_lag_ms"]) for r in rows)
    assert [r["outcome"] for r in rows] == ["success"] * 12
    assert lags[0] >= 0
    # Spin-wait measured about 0.002 ms here and a plain asyncio sleep 7 to 23 ms,
    # so 3 ms still tells them apart and leaves room for a busy machine.
    assert lags[len(lags) // 2] < 3.0


@pytest.mark.anyio
async def test_without_spin_wait_no_request_is_sent_before_its_planned_time():
    offsets = [0.013 + 0.047 * i for i in range(12)]
    with serving(stub_app(delay_s=0)) as url:
        with anyio.fail_after(5):
            rows = await send(url, hand_schedule(*offsets), spin_wait=False)

    early = [(r["request_id"], r["send_lag_ms"]) for r in rows if float(r["send_lag_ms"]) < 0]
    assert early == []


@pytest.mark.anyio
async def test_no_reply_within_the_generator_timeout_is_a_timeout_and_the_run_ends():
    with serving(stub_app(delay_s=5.0)) as url:
        with anyio.fail_after(3):
            rows = await send(url, hand_schedule(0.0, 0.1), timeout_s=0.3)

    assert [r["outcome"] for r in rows] == ["timeout", "timeout"]
    assert [r["status"] for r in rows] == ["", ""]
    assert all(250 < float(r["response_ms"]) < 1000 for r in rows)


@pytest.mark.anyio
@pytest.mark.parametrize("status, reply_outcome, outcome", [
    (200, "done", "success"),  # a worker answering directly
    (503, "rejected", "rejected"),
    (504, "expired", "expired"),
    (504, None, "timeout"),  # the dispatcher's own timeout
    (500, "error", "error"),
])
async def test_outcome_follows_the_reply_status(status, reply_outcome, outcome):
    headers = {} if reply_outcome is None else {"X-Outcome": reply_outcome}
    with serving(stub_app(delay_s=0, status=status, headers=headers)) as url:
        with anyio.fail_after(5):
            (row,) = await send(url, hand_schedule(0.0))

    assert row["status"] == str(status)
    assert row["outcome"] == outcome


@pytest.mark.anyio
async def test_request_carries_the_schedule_ids_and_reply_headers_fill_the_row():
    reply_headers = {"X-Chosen-Worker": "w2", "X-Processing-Ms": "41.250", "X-Output-Bytes": "6"}
    app = stub_app(delay_s=0, headers=reply_headers)
    with serving(app) as url:
        with anyio.fail_after(5):
            (row,) = await send(url, hand_schedule(0.0, image_id="small-01"))

    (headers,) = app.state.request_headers
    assert headers["x-request-id"] == "r00000"
    assert headers["x-image-id"] == "small-01"
    assert headers["x-size-class"] == "small"
    assert headers["content-length"] == str(len(b"small image bytes"))
    assert row["run_id"] == "test-run"
    assert (row["chosen_worker"], row["processing_ms"], row["output_bytes"]) == ("w2", "41.250", "6")


@pytest.mark.anyio
async def test_a_refused_connection_is_an_error_and_the_run_ends():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()  # nothing listens on this port now

    with anyio.fail_after(5):
        (row,) = await send(f"http://127.0.0.1:{port}/process", hand_schedule(0.0))

    assert row["outcome"] == "error"
    assert row["status"] == ""


# Small images and a 1 s run keep the command line tests quick.
TEST_CONFIG = """
stage = "pilot"

[generator]
timeout_ms = 2000
spin_wait = false

[run]
length_s = 1.0
dropped_window_s = 0.2
achieved_rate_tolerance = 0.05

[images]
per_class = 2

[images.resolutions]
small = [32, 24]
medium = [48, 32]
large = [64, 48]

[images.mix]
small = 0.4
medium = 0.4
large = 0.2

[seeds]
image_set = 1
schedule = 1
"""


def run_loadgen(tmp_path, url, out, rule="rr", round_number=1, config_text=TEST_CONFIG, rate="6", extra=()):
    config_path = tmp_path / "test.toml"
    config_path.write_text(config_text, encoding="utf-8")
    loadgen_main([
        "--config", str(config_path), "--target", url, "--scenario", "2", "--rate", rate,
        "--round", str(round_number), "--rule", rule, "--run-id", "cli-run", "--out", str(out), *extra,
    ])
    return out


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_run_folder_holds_the_schedule_the_log_and_the_run_parameters(tmp_path, capsys):
    with serving(stub_app(delay_s=0)) as url:
        out = run_loadgen(tmp_path, url, tmp_path / "run")

    schedule = read_csv(out / "schedule.csv")
    rows = read_csv(out / "generator.csv")
    with open(out / "generator.csv", newline="", encoding="utf-8") as f:
        header = next(csv.reader(f))
    info = json.loads((out / "loadgen.json").read_text(encoding="utf-8"))

    assert len(schedule) > 0
    assert header == list(GENERATOR_LOG_COLUMNS)
    assert [r["request_id"] for r in rows] == [s["request_id"] for s in schedule]
    assert {r["outcome"] for r in rows} == {"success"}
    assert {r["run_id"] for r in rows} == {"cli-run"}
    assert info == {
        "run_id": "cli-run", "rule": "rr", "scenario": 2, "rate": 6.0, "round": 1,
        "target": url, "length_s": 1.0, "dropped_window_s": 0.2,
        "achieved_rate_tolerance": 0.05, "schedule_seed": "1:2:6.0:1",
    }
    assert capsys.readouterr().out == f"sent {len(rows)} requests to {url}: {{'success': {len(rows)}}}\n"


def test_changing_only_the_rule_keeps_the_schedule_and_changing_the_round_does_not(tmp_path):
    with serving(stub_app(delay_s=0)) as url:
        rr = run_loadgen(tmp_path, url, tmp_path / "rr", rule="rr")
        lur = run_loadgen(tmp_path, url, tmp_path / "lur", rule="lur")
        round_2 = run_loadgen(tmp_path, url, tmp_path / "round-2", rule="rr", round_number=2)

    rr_bytes = (rr / "schedule.csv").read_bytes()
    assert len(read_csv(rr / "schedule.csv")) > 0
    assert (lur / "schedule.csv").read_bytes() == rr_bytes
    assert (round_2 / "schedule.csv").read_bytes() != rr_bytes


def test_an_unset_config_value_stops_the_run_before_sending(tmp_path, capsys):
    config_text = TEST_CONFIG.replace("timeout_ms = 2000\n", "")
    with pytest.raises(SystemExit):
        run_loadgen(tmp_path, "http://127.0.0.1:9/process", tmp_path / "run", config_text=config_text)

    assert "generator.timeout_ms" in capsys.readouterr().err
    assert not (tmp_path / "run").exists()


def test_run_length_flag_shortens_the_run_and_scales_the_dropped_window(tmp_path):
    with serving(stub_app(delay_s=0)) as url:
        out = run_loadgen(tmp_path, url, tmp_path / "run", rate="20", extra=["--run-length", "0.5"])

    info = json.loads((out / "loadgen.json").read_text(encoding="utf-8"))
    offsets = [float(s["planned_offset_s"]) for s in read_csv(out / "schedule.csv")]
    # The config has a 1 s run with W = 0.2 s, so a 0.5 s run gets W = 0.1 s.
    assert info["length_s"] == 0.5
    assert info["dropped_window_s"] == pytest.approx(0.1)
    assert offsets and max(offsets) < 0.5


def test_a_main_stage_config_refuses_the_run_length_flag(tmp_path, capsys):
    config_path = committed_repo(tmp_path, full_main_config_text())
    with pytest.raises(SystemExit):
        loadgen_main([
            "--config", str(config_path), "--target", "http://127.0.0.1:9/process", "--scenario", "2",
            "--rate", "2", "--round", "1", "--rule", "rr", "--run-id", "main-run",
            "--out", str(tmp_path / "run"), "--run-length", "5",
        ])

    assert "--run-length" in capsys.readouterr().err
    assert not (tmp_path / "run").exists()


def test_a_rule_name_with_a_typo_is_refused(tmp_path, capsys):
    with pytest.raises(SystemExit):
        run_loadgen(tmp_path, "http://127.0.0.1:9/process", tmp_path / "run", rule="feedbak")

    assert "--rule" in capsys.readouterr().err
    assert not (tmp_path / "run").exists()


def test_a_rate_of_0_is_refused(tmp_path, capsys):
    with pytest.raises(SystemExit):
        run_loadgen(tmp_path, "http://127.0.0.1:9/process", tmp_path / "run", rate="0")

    assert "--rate" in capsys.readouterr().err
    assert not (tmp_path / "run").exists()
