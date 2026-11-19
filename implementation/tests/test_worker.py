import asyncio
import csv
import io
import threading
from contextlib import asynccontextmanager

import anyio
import httpx
import pytest
from PIL import Image

from plb import protocol
from worker.app import create_app
from worker.imaging import process_jpeg

pytestmark = pytest.mark.anyio


def jpeg(width, height):
    image = Image.radial_gradient("L").resize((width, height)).convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


@asynccontextmanager
async def running(app):
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://worker") as client:
            yield client


def process_request(client, request_id, body, budget_ms=10_000):
    headers = {protocol.REQUEST_ID: request_id, protocol.BUDGET_MS: str(budget_ms)}
    return client.post("/process", content=body, headers=headers)


async def test_reply_is_a_half_size_jpeg_with_processing_time():
    async with running(create_app(queue_capacity=2)) as client:
        reply = await process_request(client, "r1", jpeg(161, 91))

    assert reply.status_code == 200
    assert reply.headers["content-type"] == "image/jpeg"
    assert reply.headers[protocol.OUTCOME] == protocol.DONE
    assert float(reply.headers[protocol.PROCESSING_MS]) > 0
    assert int(reply.headers[protocol.OUTPUT_BYTES]) == len(reply.content)
    with Image.open(io.BytesIO(reply.content)) as output:
        assert output.format == "JPEG"
        assert output.size == (80, 45)


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


async def flush(client, path):
    reply = await client.post("/admin/flush", json={"path": str(path)})
    assert reply.status_code == 200
    return read_rows(path)


async def test_two_identical_requests_are_both_processed(tmp_path):
    body = jpeg(120, 80)
    async with running(create_app(queue_capacity=2)) as client:
        first = await process_request(client, "same-1", body)
        second = await process_request(client, "same-2", body)
        rows = await flush(client, tmp_path / "worker.csv")

    assert first.status_code == second.status_code == 200
    assert [(r["request_id"], r["outcome"]) for r in rows] == [("same-1", "done"), ("same-2", "done")]
    assert all(float(r["processing_ms"]) > 0 for r in rows)


class GatedProcess:
    """Real Pillow work that waits for the test to open a gate first.

    It counts calls so a test can tell whether a request ever reached Pillow.
    """

    def __init__(self):
        self.started = threading.Event()
        self.release = threading.Event()
        self.request_bodies = []

    def __call__(self, data):
        self.request_bodies.append(data)
        self.started.set()
        assert self.release.wait(timeout=10)
        return process_jpeg(data)


async def start_blocking_request(client, gate, body):
    """Send a request that holds the processing slot until the gate opens."""
    task = asyncio.create_task(process_request(client, "running", body))
    assert await asyncio.to_thread(gate.started.wait, 5)
    return task


async def test_full_queue_rejects_at_once_with_503():
    gate = GatedProcess()
    body = jpeg(120, 80)
    async with running(create_app(queue_capacity=1, process=gate)) as client:
        running_task = await start_blocking_request(client, gate, body)
        queued_task = asyncio.create_task(process_request(client, "queued", body))
        await asyncio.sleep(0.1)  # let the second request reach the queue

        with anyio.fail_after(2):
            rejected = await process_request(client, "extra", body)
        still_running = not running_task.done()

        gate.release.set()
        replies = await asyncio.gather(running_task, queued_task)

    assert rejected.status_code == 503
    assert rejected.headers[protocol.OUTCOME] == protocol.REJECTED
    assert still_running
    assert [r.status_code for r in replies] == [200, 200]


async def test_queued_request_past_its_budget_expires_without_image_work(tmp_path):
    gate = GatedProcess()
    async with running(create_app(queue_capacity=1, process=gate)) as client:
        running_task = await start_blocking_request(client, gate, jpeg(120, 80))
        late_task = asyncio.create_task(process_request(client, "late", jpeg(100, 60), budget_ms=50))
        await asyncio.sleep(0.2)  # the budget passes while "late" waits

        gate.release.set()
        running_reply, late = await asyncio.gather(running_task, late_task)
        rows = await flush(client, tmp_path / "worker.csv")

    assert running_reply.status_code == 200
    assert late.status_code == 504
    assert late.headers[protocol.OUTCOME] == protocol.EXPIRED
    assert len(gate.request_bodies) == 1  # only the running request reached Pillow
    late_row = next(r for r in rows if r["request_id"] == "late")
    assert late_row["outcome"] == "expired"
    assert float(late_row["queue_wait_ms"]) > 50


async def test_health_returns_200_without_image_work():
    gate = GatedProcess()
    gate.release.set()
    async with running(create_app(queue_capacity=1, process=gate)) as client:
        reply = await client.get("/health")

    assert reply.status_code == 200
    assert gate.request_bodies == []


async def test_flush_writes_one_row_per_request_with_the_log_columns(tmp_path):
    gate = GatedProcess()
    path = tmp_path / "worker.csv"
    async with running(create_app(queue_capacity=1, process=gate)) as client:
        running_task = await start_blocking_request(client, gate, jpeg(120, 80))
        late_task = asyncio.create_task(process_request(client, "late", jpeg(100, 60), budget_ms=50))
        await asyncio.sleep(0.2)
        await process_request(client, "extra", jpeg(100, 60))
        gate.release.set()
        await asyncio.gather(running_task, late_task)
        rows = await flush(client, path)

    with open(path, newline="", encoding="utf-8") as f:
        header = next(csv.reader(f))
    assert header == ["request_id", "arrival_unix_s", "queue_wait_ms", "processing_ms", "outcome"]
    assert sorted((r["request_id"], r["outcome"]) for r in rows) == [
        ("extra", "rejected"), ("late", "expired"), ("running", "done"),
    ]


async def test_log_is_written_on_shutdown(tmp_path):
    path = tmp_path / "shutdown.csv"
    app = create_app(queue_capacity=1, shutdown_log_path=path)
    async with running(app) as client:
        await process_request(client, "r1", jpeg(120, 80))

    assert [(r["request_id"], r["outcome"]) for r in read_rows(path)] == [("r1", "done")]


async def test_a_body_that_is_not_an_image_fails_alone(tmp_path):
    async with running(create_app(queue_capacity=1)) as client:
        with anyio.fail_after(5):
            broken = await process_request(client, "broken", b"not a jpeg")
            after = await process_request(client, "after", jpeg(120, 80))
        rows = await flush(client, tmp_path / "worker.csv")

    assert broken.status_code == 500
    assert broken.headers[protocol.OUTCOME] == protocol.ERROR
    assert after.status_code == 200
    assert [(r["request_id"], r["outcome"]) for r in rows] == [("broken", "error"), ("after", "done")]


async def test_flush_creates_missing_folders(tmp_path):
    path = tmp_path / "run-1" / "logs" / "worker.csv"
    async with running(create_app(queue_capacity=1)) as client:
        await process_request(client, "r1", jpeg(120, 80))
        rows = await flush(client, path)

    assert [r["request_id"] for r in rows] == ["r1"]


async def test_a_budget_that_is_not_a_number_is_refused_and_logged(tmp_path):
    headers = {protocol.REQUEST_ID: "bad-budget", protocol.BUDGET_MS: "soon"}
    async with running(create_app(queue_capacity=1)) as client:
        reply = await client.post("/process", content=jpeg(120, 80), headers=headers)
        rows = await flush(client, tmp_path / "worker.csv")

    assert reply.status_code == 400
    assert reply.headers[protocol.OUTCOME] == protocol.ERROR
    assert [(r["request_id"], r["outcome"]) for r in rows] == [("bad-budget", "error")]
