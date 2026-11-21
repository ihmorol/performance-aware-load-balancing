import asyncio
import socket
import threading
import time
from contextlib import contextmanager

import anyio
import pytest
import uvicorn
from fastapi import FastAPI, Request, Response

from experiments.loadgen import send_schedule
from experiments.schedule import PlannedRequest


def stub_app(delay_s, status=200, headers=None):
    """A target that waits delay_s before each reply and records arrivals."""
    app = FastAPI()
    app.state.arrivals = []

    @app.post("/process")
    async def process(request: Request) -> Response:
        app.state.arrivals.append(dict(request.headers))
        await request.body()
        await asyncio.sleep(delay_s)
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
    with serving(stub_app(delay_s=2.0)) as url:
        with anyio.fail_after(10):
            rows = await send(url, hand_schedule(0.0, 0.5, 1.0, 1.5))

    first_reply_s = min(float(r["planned_offset_s"]) + float(r["response_ms"]) / 1000 for r in rows)
    sent_after_first_reply = [r["request_id"] for r in rows if float(r["actual_offset_s"]) >= first_reply_s]
    assert [r["outcome"] for r in rows] == ["success"] * 4
    # asyncio's clock moves in steps of about 15 ms on Windows, so the stub's
    # 2 s sleep can end a little early.
    assert first_reply_s > 1.9
    assert sent_after_first_reply == []


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
    assert abs(float(row["actual_offset_s"]) - (0.1 + send_lag_ms / 1000)) < 0.002


@pytest.mark.anyio
async def test_with_spin_wait_requests_go_out_on_time_and_never_early():
    offsets = [0.013 + 0.047 * i for i in range(12)]
    with serving(stub_app(delay_s=0)) as url:
        with anyio.fail_after(5):
            rows = await send(url, hand_schedule(*offsets), spin_wait=True)

    lags = sorted(float(r["send_lag_ms"]) for r in rows)
    assert [r["outcome"] for r in rows] == ["success"] * 12
    assert lags[0] >= 0
    # A plain asyncio sleep is often 10 ms or more off on Windows.
    assert lags[len(lags) // 2] < 1.0


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
    (502, None, "error"),
    (500, "error", "error"),
])
async def test_outcome_follows_the_reply_status(status, reply_outcome, outcome):
    headers = {} if reply_outcome is None else {"X-Outcome": reply_outcome}
    with serving(stub_app(delay_s=0, status=status, headers=headers)) as url:
        with anyio.fail_after(5):
            (row,) = await send(url, hand_schedule(0.0))

    assert row["status"] == str(status)
    assert row["outcome"] == outcome
    assert float(row["response_ms"]) > 0


@pytest.mark.anyio
async def test_request_carries_the_schedule_ids_and_reply_headers_fill_the_row():
    reply_headers = {"X-Chosen-Worker": "w2", "X-Processing-Ms": "41.250", "X-Output-Bytes": "6"}
    app = stub_app(delay_s=0, headers=reply_headers)
    with serving(app) as url:
        with anyio.fail_after(5):
            (row,) = await send(url, hand_schedule(0.0, image_id="small-01"))

    (arrival,) = app.state.arrivals
    assert arrival["x-request-id"] == "r00000"
    assert arrival["x-image-id"] == "small-01"
    assert arrival["x-size-class"] == "small"
    assert arrival["content-length"] == str(len(b"small image bytes"))
    assert row["run_id"] == "test-run"
    assert (row["chosen_worker"], row["processing_ms"], row["output_bytes"]) == ("w2", "41.250", "6")


@pytest.mark.anyio
async def test_reply_header_columns_stay_empty_when_the_reply_has_none():
    with serving(stub_app(delay_s=0)) as url:
        with anyio.fail_after(5):
            (row,) = await send(url, hand_schedule(0.0))

    assert (row["chosen_worker"], row["processing_ms"], row["output_bytes"]) == ("", "", "")


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
