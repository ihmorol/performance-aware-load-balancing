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
from pydantic import BaseModel

from dispatcher.rules import RuleState, WorkerView, select, update_estimate
from plb import protocol
from plb.config import Config
from plb.rows import DISPATCHER_LOG_COLUMNS

WORKER_NAMES = ("w1", "w2")


class FlushRequest(BaseModel):
    path: str


@dataclass
class WorkerState:
    url: str
    unfinished: int = 0
    estimate_ms: float | None = None  # None until the first sample


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
) -> FastAPI:
    """Build a dispatcher app.

    The worker addresses, timeout, EWMA weight, probe threshold, warm-up
    count, and the scenario's weights come from config. transport is for
    tests, which put fake workers behind it.
    """
    workers = [WorkerState(url) for url in config.addresses.workers]
    rule_state = RuleState()
    client: httpx.AsyncClient | None = None
    log: list[dict] = []

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
        worker.estimate_ms = update_estimate(
            worker.estimate_ms, float(reply.headers[protocol.PROCESSING_MS]), config.dispatcher.ewma_weight,
        )
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

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI):
        nonlocal client
        client = httpx.AsyncClient(transport=transport)
        try:
            yield
        finally:
            await client.aclose()

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

    @app.post("/admin/flush")
    async def flush_endpoint(flush: FlushRequest) -> dict:
        write_log(log, flush.path)
        return {"path": flush.path, "rows": len(log)}

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
