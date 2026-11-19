"""Worker service: one processing slot in front of a bounded queue.

POST /process takes JPEG bytes. One consumer task takes requests from the
queue in arrival order and runs the image work in a thread, so the event loop
keeps accepting requests while an image is processed. Only the image work is
timed. Nothing is cached, so identical requests cost the same work.
"""

from __future__ import annotations

import asyncio
import contextlib
import csv
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

from plb import protocol
from worker.imaging import process_jpeg


# Columns of the worker log. arrival_unix_s is wall-clock time, kept only to
# line rows up with other logs from the same machine; queue_wait_ms and
# processing_ms come from time.perf_counter, a monotonic clock.
LOG_COLUMNS = ("request_id", "arrival_unix_s", "queue_wait_ms", "processing_ms", "outcome")


class FlushRequest(BaseModel):
    path: str


@dataclass
class _Job:
    request_id: str
    body: bytes
    # time.perf_counter() at arrival. It is a monotonic clock, and unlike
    # time.monotonic() on Windows it does not move in steps of about 15 ms.
    arrival: float
    arrival_unix: float
    budget_ms: float | None  # None when the request carries no budget header
    reply: asyncio.Future = field(default_factory=lambda: asyncio.get_running_loop().create_future())


def create_app(
    queue_capacity: int,
    process: Callable[[bytes], bytes] = process_jpeg,
    shutdown_log_path: str | Path | None = None,
) -> FastAPI:
    """Build a worker app.

    queue_capacity is the number of requests that may wait behind the one
    being processed. process does the image work; tests pass their own.
    When shutdown_log_path is given, the log is written there on shutdown.
    """
    if queue_capacity < 1:
        raise ValueError("queue_capacity must be at least 1")

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.queue = asyncio.Queue(maxsize=queue_capacity)
        consumer = asyncio.create_task(_consume(app.state.queue, process, log))
        try:
            yield
        finally:
            consumer.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await consumer
            if shutdown_log_path is not None:
                write_log(log, shutdown_log_path)

    log: list[dict] = []
    app = FastAPI(lifespan=lifespan)

    @app.post("/process")
    async def process_endpoint(request: Request) -> Response:
        arrival, arrival_unix = time.perf_counter(), time.time()
        job = _Job(
            request_id=request.headers.get(protocol.REQUEST_ID, ""),
            body=await request.body(),
            arrival=arrival,
            arrival_unix=arrival_unix,
            budget_ms=_budget_ms(request),
        )
        try:
            request.app.state.queue.put_nowait(job)
        except asyncio.QueueFull:
            _record(log, job, protocol.REJECTED)
            return Response(status_code=503, headers={protocol.OUTCOME: protocol.REJECTED})
        return await job.reply

    @app.get("/health")
    async def health() -> dict:
        # No image work here, so health checks never disturb measurements.
        return {"status": "ok"}

    @app.post("/admin/flush")
    async def flush_endpoint(flush: FlushRequest) -> dict:
        write_log(log, flush.path)
        return {"path": flush.path, "rows": len(log)}

    return app


def write_log(log: list[dict], path: str | Path) -> None:
    """Write every log row so far to a CSV file, replacing the file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_COLUMNS)
        writer.writeheader()
        writer.writerows(log)


async def _consume(queue: asyncio.Queue, process: Callable[[bytes], bytes], log: list[dict]) -> None:
    while True:
        job: _Job = await queue.get()
        queue_wait_ms = (time.perf_counter() - job.arrival) * 1000
        if job.budget_ms is not None and queue_wait_ms > job.budget_ms:
            # Nobody is waiting for this reply any more, so skip the image work.
            _record(log, job, protocol.EXPIRED, queue_wait_ms)
            _reply(job, Response(status_code=504, headers={protocol.OUTCOME: protocol.EXPIRED}))
            continue
        try:
            output, seconds = await asyncio.to_thread(_timed, process, job.body)
        except Exception:
            # A body Pillow can't handle fails alone; the consumer keeps going.
            _record(log, job, protocol.ERROR, queue_wait_ms)
            _reply(job, Response(status_code=500, headers={protocol.OUTCOME: protocol.ERROR}))
            continue
        _record(log, job, protocol.DONE, queue_wait_ms, seconds * 1000)
        _reply(job, Response(
            content=output,
            media_type="image/jpeg",
            headers={
                protocol.OUTCOME: protocol.DONE,
                protocol.PROCESSING_MS: f"{seconds * 1000:.3f}",
                protocol.OUTPUT_BYTES: str(len(output)),
            },
        ))


def _reply(job: _Job, response: Response) -> None:
    # The handler's wait is cancelled if the client goes away first.
    if not job.reply.done():
        job.reply.set_result(response)


def _budget_ms(request: Request) -> float | None:
    value = request.headers.get(protocol.BUDGET_MS)
    return None if value is None else float(value)


def _record(log: list[dict], job: _Job, outcome: str, queue_wait_ms: float | None = None,
            processing_ms: float | None = None) -> None:
    log.append({
        "request_id": job.request_id,
        "arrival_unix_s": f"{job.arrival_unix:.6f}",
        "queue_wait_ms": "" if queue_wait_ms is None else f"{queue_wait_ms:.3f}",
        "processing_ms": "" if processing_ms is None else f"{processing_ms:.3f}",
        "outcome": outcome,
    })


def _timed(process: Callable[[bytes], bytes], body: bytes) -> tuple[bytes, float]:
    start = time.perf_counter()
    output = process(body)
    return output, time.perf_counter() - start
