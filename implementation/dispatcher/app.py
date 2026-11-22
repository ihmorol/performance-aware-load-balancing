"""Dispatcher service: one forwarding path shared by all four rules.

Only the select() step differs between rules (see dispatcher/rules.py).
"""

from __future__ import annotations

import asyncio
import contextlib
import csv
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from dispatcher.rules import RuleState, WorkerView, select, update_estimate
from plb import protocol
from plb.config import Config
from plb.images import generate_image
from plb.rows import DISPATCHER_LOG_COLUMNS

WORKER_NAMES = ("w1", "w2")

# The status the dispatcher replies with for each outcome.
STATUS = {
    protocol.SUCCESS: 200,
    protocol.REJECTED: 503,
    protocol.EXPIRED: 504,
    protocol.TIMEOUT: 504,
    protocol.ERROR: 502,
}


class FlushRequest(BaseModel):
    path: str


@dataclass
class WorkerState:
    url: str
    unfinished: int = 0
    estimate_ms: float | None = None
    # time.perf_counter() of the last reply that fed the estimate.
    last_completion_s: float | None = None
    probes_sent: int = 0


@dataclass
class Job:
    """A client request, warm-up request, or probe."""
    request_id: str
    image_id: str
    size_class: str
    body: bytes
    probe: bool = False
    warmup: bool = False


@dataclass
class Result:
    outcome: str
    reply: httpx.Response | None  # None when no reply came


def create_app(
    config: Config,
    rule: str,
    scenario: int,
    rate: float,
    run_id: str,
    transport: httpx.AsyncBaseTransport | None = None,
    shutdown_log_path: str | Path | None = None,
) -> FastAPI:
    """Build a dispatcher app.

    transport is for tests, which put fake workers behind it. When
    shutdown_log_path is given, the log is written there on shutdown.
    """
    workers = [WorkerState(url) for url in config.addresses.workers]
    rule_state = RuleState(weights=getattr(config.weights, f"scenario{scenario}"))
    client: httpx.AsyncClient | None = None
    log: list[dict] = []
    health = "warming up"  # then "ok", or "warm-up failed" for good
    # Probes wait for the first client request, so idle workers are not probed
    # while the orchestrator is still getting the run ready.
    client_request_seen = False
    warmup_image = generate_image(config.images, config.seeds.image_set, "medium", 0)
    probe_image = generate_image(config.images, config.seeds.image_set, "small", 0)

    async def forward(index: int, job: Job) -> Result:
        """Send one job to one worker. No retries."""
        worker = workers[index]
        headers = {
            protocol.REQUEST_ID: job.request_id,
            protocol.IMAGE_ID: job.image_id,
            protocol.SIZE_CLASS: job.size_class,
            protocol.BUDGET_MS: str(config.dispatcher.timeout_ms),
            protocol.PROBE: "1" if job.probe else "0",
        }
        worker.unfinished += 1
        try:
            # wait_for enforces D.
            reply = await asyncio.wait_for(
                client.post(worker.url + "/process", content=job.body, headers=headers),
                timeout=config.dispatcher.timeout_ms / 1000,
            )
        except TimeoutError:
            return Result(protocol.TIMEOUT, None)
        except httpx.HTTPError:
            return Result(protocol.ERROR, None)
        finally:
            worker.unfinished -= 1

        if reply.status_code == 503:
            return Result(protocol.REJECTED, reply)
        if reply.status_code == 504 and reply.headers.get(protocol.OUTCOME) == protocol.EXPIRED:
            return Result(protocol.EXPIRED, reply)
        if reply.status_code != 200:
            return Result(protocol.ERROR, reply)
        try:
            processing_ms = float(reply.headers[protocol.PROCESSING_MS])
        except (KeyError, ValueError):
            return Result(protocol.ERROR, reply)
        # Updated under every rule, though only the feedback rule reads it.
        worker.estimate_ms = update_estimate(worker.estimate_ms, processing_ms, config.dispatcher.ewma_weight)
        worker.last_completion_s = time.perf_counter()
        return Result(protocol.SUCCESS, reply)

    async def send(job: Job, index: int | None = None) -> tuple[int, Result]:
        """Send a job and log it. select() picks the worker when index is None;
        warm-up requests and probes pass a fixed index."""
        nonlocal rule_state
        start_s = time.perf_counter()
        seen = tuple(WorkerView(w.unfinished, w.estimate_ms) for w in workers)
        select_ns = ""
        if index is None:
            select_start = time.perf_counter_ns()
            index, rule_state = select(rule, seen, rule_state)
            select_ns = time.perf_counter_ns() - select_start
        result = await forward(index, job)
        reply = result.reply
        log.append({
            "run_id": run_id,
            "rule": rule,
            "scenario": scenario,
            "rate": rate,
            "request_id": job.request_id,
            "image_id": job.image_id,
            "size_class": job.size_class,
            "probe": "1" if job.probe else "0",
            "warmup": "1" if job.warmup else "0",
            "chosen_worker": WORKER_NAMES[index],
            "unfinished_w1": seen[0].unfinished,
            "unfinished_w2": seen[1].unfinished,
            "estimate_w1_ms": _ms(seen[0].estimate_ms),
            "estimate_w2_ms": _ms(seen[1].estimate_ms),
            "select_ns": select_ns,
            "worker_processing_ms": reply.headers.get(protocol.PROCESSING_MS, "") if reply else "",
            "worker_status": reply.status_code if reply else "",
            "outcome": result.outcome,
            "dispatcher_ms": _ms((time.perf_counter() - start_s) * 1000),
        })
        return index, result

    async def warm_up() -> bool:
        all_succeeded = True
        for index, name in enumerate(WORKER_NAMES):
            for n in range(config.dispatcher.warmup_count):
                job = Job(f"warmup-{name}-{n}", warmup_image.image_id, warmup_image.size_class,
                          warmup_image.data, warmup=True)
                _, result = await send(job, index)
                all_succeeded = all_succeeded and result.outcome == protocol.SUCCESS
        return all_succeeded

    async def probe_loop() -> None:
        threshold_s = config.dispatcher.probe_threshold_s
        while True:
            await asyncio.sleep(threshold_s / 4)
            if not client_request_seen:
                continue
            for index, worker in enumerate(workers):
                # A worker that never completed anything counts as idle.
                last = worker.last_completion_s
                idle = last is None or time.perf_counter() - last >= threshold_s
                if idle and worker.unfinished == 0:
                    # Awaited, not a task: the probe counts as unfinished at
                    # once, and no probe can be in flight during a check.
                    job = Job(f"probe-{WORKER_NAMES[index]}-{worker.probes_sent}", probe_image.image_id,
                              probe_image.size_class, probe_image.data, probe=True)
                    worker.probes_sent += 1
                    await send(job, index)

    async def start_up() -> None:
        nonlocal health
        if not await warm_up():
            health = "warm-up failed"
            return
        health = "ok"
        if rule == "feedback":
            await probe_loop()

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI):
        nonlocal client
        # No HTTPX timeout: its default of 5 s could end a request before D.
        client = httpx.AsyncClient(transport=transport, timeout=None)
        # Warm-up runs in the background so /health can answer meanwhile.
        background = asyncio.create_task(start_up())
        try:
            yield
        finally:
            background.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await background
            await client.aclose()
            if shutdown_log_path is not None:
                write_log(log, shutdown_log_path)

    app = FastAPI(lifespan=lifespan)

    @app.post("/process")
    async def process_endpoint(request: Request) -> Response:
        nonlocal client_request_seen
        client_request_seen = True
        job = Job(
            request_id=request.headers.get(protocol.REQUEST_ID, ""),
            image_id=request.headers.get(protocol.IMAGE_ID, ""),
            size_class=request.headers.get(protocol.SIZE_CLASS, ""),
            # Read in full before send(), so dispatcher_ms starts after it.
            body=await request.body(),
        )
        index, result = await send(job)
        return _reply(result, index)

    @app.get("/health")
    async def health_endpoint() -> JSONResponse:
        return JSONResponse({"status": health}, status_code=200 if health == "ok" else 503)

    @app.post("/admin/flush")
    async def flush_endpoint(flush: FlushRequest) -> dict:
        write_log(log, flush.path)
        return {"path": flush.path, "rows": len(log)}

    @app.get("/admin/cpu")
    async def cpu_endpoint() -> dict:
        # Read by the orchestrator at the start and end of each run.
        return {"cpu_s": time.process_time()}

    return app


def write_log(log: list[dict], path: str | Path) -> None:
    """Write every log row so far to a CSV file, replacing the file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DISPATCHER_LOG_COLUMNS)
        writer.writeheader()
        writer.writerows(log)


def _reply(result: Result, index: int) -> Response:
    headers = {protocol.OUTCOME: result.outcome, protocol.CHOSEN_WORKER: WORKER_NAMES[index]}
    status = STATUS[result.outcome]
    if result.reply is None:
        return Response(status_code=status, headers=headers)
    for name in (protocol.PROCESSING_MS, protocol.OUTPUT_BYTES):
        if name in result.reply.headers:
            headers[name] = result.reply.headers[name]
    return Response(result.reply.content, status_code=status, headers=headers,
                    media_type=result.reply.headers.get("content-type"))


def _ms(value: float | None) -> str:
    return "" if value is None else f"{value:.3f}"
