"""Dispatcher service: one forwarding path shared by all four rules.

POST /process reads the whole body, picks a worker with select(), forwards
the request with one shared HTTPX client, and passes the reply back. Only the
select() step differs between rules.
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


class FlushRequest(BaseModel):
    path: str


@dataclass
class WorkerState:
    url: str
    unfinished: int = 0
    estimate_ms: float | None = None  # None until the first sample
    # time.perf_counter() of the last reply that fed the estimate.
    last_completion_s: float | None = None
    probe_in_flight: bool = False
    probes_sent: int = 0


@dataclass
class Job:
    """One request to send to a worker: a client request, warm-up, or probe."""
    request_id: str
    image_id: str
    size_class: str
    body: bytes
    probe: bool = False
    warmup: bool = False


@dataclass
class Result:
    outcome: str
    status: int  # the status the dispatcher replies with
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

    The worker addresses, timeout, EWMA weight, probe threshold, warm-up
    count, and the scenario's weights come from config. rule is one of
    RULES. scenario, rate, and run_id go into every log row. transport is
    for tests, which put fake workers behind it. When shutdown_log_path is
    given, the log is written there on shutdown.
    """
    workers = [WorkerState(url) for url in config.addresses.workers]
    # Weights are only read by weighted round-robin.
    rule_state = RuleState(weights=getattr(config.weights, f"scenario{scenario}"))
    client: httpx.AsyncClient | None = None
    log: list[dict] = []
    health = "warming up"  # then "ok", or "warm-up failed" for good
    warmup_image = generate_image(config.images, config.seeds.image_set, "medium", 0)
    probe_image = generate_image(config.images, config.seeds.image_set, "small", 0)
    probes: set[asyncio.Task] = set()  # probe tasks still running

    def snapshot() -> tuple[WorkerView, WorkerView]:
        return tuple(WorkerView(w.unfinished, w.estimate_ms) for w in workers)

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
        # Counted from assignment until any outcome, timeout and errors too.
        worker.unfinished += 1
        try:
            # wait_for enforces D. The HTTPX timeout is not enough on its
            # own: the in-process transport the tests use ignores it.
            reply = await asyncio.wait_for(
                client.post(worker.url + "/process", content=job.body, headers=headers),
                timeout=config.dispatcher.timeout_ms / 1000,
            )
        except TimeoutError:
            return Result(protocol.TIMEOUT, 504, None)
        except httpx.HTTPError:
            return Result(protocol.ERROR, 502, None)
        finally:
            worker.unfinished -= 1

        if reply.status_code == 503:
            return Result(protocol.REJECTED, 503, reply)
        if reply.status_code == 504 and reply.headers.get(protocol.OUTCOME) == protocol.EXPIRED:
            return Result(protocol.EXPIRED, 504, reply)
        if reply.status_code != 200:
            return Result(protocol.ERROR, 502, reply)
        # Updated under every rule, though only the feedback rule reads it.
        worker.estimate_ms = update_estimate(
            worker.estimate_ms, float(reply.headers[protocol.PROCESSING_MS]), config.dispatcher.ewma_weight,
        )
        worker.last_completion_s = time.perf_counter()
        return Result(protocol.SUCCESS, 200, reply)

    def record(job: Job, index: int, seen: tuple[WorkerView, WorkerView], select_ns: int | None,
               result: Result, start_s: float) -> None:
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
            "select_ns": "" if select_ns is None else select_ns,
            "worker_processing_ms": reply.headers.get(protocol.PROCESSING_MS, "") if reply else "",
            "worker_status": reply.status_code if reply else "",
            "outcome": result.outcome,
            "dispatcher_ms": _ms((time.perf_counter() - start_s) * 1000),
        })

    async def send_without_select(index: int, job: Job) -> Result:
        """Forward a warm-up request or probe, which go to a fixed worker."""
        start_s = time.perf_counter()
        seen = snapshot()
        result = await forward(index, job)
        record(job, index, seen, None, result, start_s)
        return result

    async def warm_up() -> bool:
        """Send K requests with the same medium image to each worker in turn."""
        all_succeeded = True
        for index, name in enumerate(WORKER_NAMES):
            for n in range(config.dispatcher.warmup_count):
                job = Job(f"warmup-{name}-{n}", warmup_image.image_id, warmup_image.size_class,
                          warmup_image.data, warmup=True)
                result = await send_without_select(index, job)
                all_succeeded = all_succeeded and result.outcome == protocol.SUCCESS
        return all_succeeded

    async def probe(index: int) -> None:
        worker = workers[index]
        job = Job(f"probe-{WORKER_NAMES[index]}-{worker.probes_sent}", probe_image.image_id,
                  probe_image.size_class, probe_image.data, probe=True)
        worker.probes_sent += 1
        try:
            await send_without_select(index, job)
        finally:
            worker.probe_in_flight = False

    async def probe_loop() -> None:
        """Probe a worker with no completion for T seconds and nothing unfinished."""
        threshold_s = config.dispatcher.probe_threshold_s
        while True:
            await asyncio.sleep(threshold_s / 4)
            now = time.perf_counter()
            for index, worker in enumerate(workers):
                # A worker that never completed anything counts as idle.
                idle = worker.last_completion_s is None or now - worker.last_completion_s >= threshold_s
                if idle and worker.unfinished == 0 and not worker.probe_in_flight:
                    worker.probe_in_flight = True
                    # A task per probe, so a slow probe doesn't hold up the
                    # check of the other worker.
                    task = asyncio.create_task(probe(index))
                    probes.add(task)
                    task.add_done_callback(probes.discard)

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
        # forward() enforces D itself.
        client = httpx.AsyncClient(transport=transport, timeout=None)
        # Warm-up runs in the background so /health can answer meanwhile.
        background = asyncio.create_task(start_up())
        try:
            yield
        finally:
            tasks = [background, *probes]
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            await client.aclose()
            if shutdown_log_path is not None:
                write_log(log, shutdown_log_path)

    app = FastAPI(lifespan=lifespan)

    @app.post("/process")
    async def process_endpoint(request: Request) -> Response:
        nonlocal rule_state
        body = await request.body()
        # dispatcher_ms is timed from here, after the body has been read.
        start_s = time.perf_counter()
        job = Job(
            request_id=request.headers.get(protocol.REQUEST_ID, ""),
            image_id=request.headers.get(protocol.IMAGE_ID, ""),
            size_class=request.headers.get(protocol.SIZE_CLASS, ""),
            body=body,
        )
        seen = snapshot()
        select_start = time.perf_counter_ns()
        index, rule_state = select(rule, seen, rule_state)
        select_ns = time.perf_counter_ns() - select_start

        result = await forward(index, job)
        record(job, index, seen, select_ns, result, start_s)
        return _reply(result, index)

    @app.get("/health")
    async def health_endpoint() -> JSONResponse:
        # 200 only after every warm-up request succeeded.
        return JSONResponse({"status": health}, status_code=200 if health == "ok" else 503)

    @app.post("/admin/flush")
    async def flush_endpoint(flush: FlushRequest) -> dict:
        write_log(log, flush.path)
        return {"path": flush.path, "rows": len(log)}

    @app.get("/admin/cpu")
    async def cpu_endpoint() -> dict:
        # CPU time of this process, read at the start and end of each run.
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
    """The dispatcher's reply: the worker's body plus the routing headers."""
    headers = {protocol.OUTCOME: result.outcome, protocol.CHOSEN_WORKER: WORKER_NAMES[index]}
    if result.reply is None:
        return Response(status_code=result.status, headers=headers)
    for name in (protocol.PROCESSING_MS, protocol.OUTPUT_BYTES):
        if name in result.reply.headers:
            headers[name] = result.reply.headers[name]
    return Response(
        result.reply.content, status_code=result.status, headers=headers,
        media_type=result.reply.headers.get("content-type"),
    )


def _ms(value: float | None) -> str:
    return "" if value is None else f"{value:.3f}"
