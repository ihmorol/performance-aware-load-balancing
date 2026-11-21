import asyncio
import csv
from contextlib import asynccontextmanager

import anyio
import httpx
import pytest
from fastapi import FastAPI, Request, Response

from dispatcher.app import create_app
from plb import protocol
from plb.rows import DISPATCHER_LOG_COLUMNS
from plb.config import (
    AddressesConfig, Config, DispatcherConfig, ImagesConfig, ResolutionsConfig, SeedsConfig, WeightsConfig,
)

pytestmark = pytest.mark.anyio

D_MS = 300  # dispatcher timeout in these tests


def make_config(warmup_count=0, probe_threshold_s=0.2, ewma_weight=0.5, weights=(1, 1), timeout_ms=D_MS):
    return Config(
        stage="pilot",
        addresses=AddressesConfig(workers=("http://w1", "http://w2")),
        dispatcher=DispatcherConfig(
            timeout_ms=timeout_ms, ewma_weight=ewma_weight,
            probe_threshold_s=probe_threshold_s, warmup_count=warmup_count,
        ),
        weights=WeightsConfig(scenario1=weights, scenario2=weights, scenario3=weights),
        # Tiny images keep the tests fast; the fake workers don't decode them.
        images=ImagesConfig(resolutions=ResolutionsConfig(small=(32, 24), medium=(64, 48), large=(96, 72))),
        seeds=SeedsConfig(image_set=1),
    )


class FakeWorker:
    """A worker whose reply each test sets. It records every call it gets."""

    def __init__(self, status=200, delay_s=0.0, processing_ms="100.000", outcome=protocol.DONE):
        self.status = status
        self.delay_s = delay_s
        self.processing_ms = processing_ms
        self.outcome = outcome
        self.refuse_connections = False
        self.calls = []  # (headers, body) per call
        self.app = FastAPI()
        self.app.post("/process")(self.process)

    async def process(self, request: Request) -> Response:
        self.calls.append((request.headers, await request.body()))
        await asyncio.sleep(self.delay_s)
        headers = {protocol.OUTCOME: self.outcome}
        if self.status == 200:
            headers[protocol.PROCESSING_MS] = self.processing_ms
            headers[protocol.OUTPUT_BYTES] = "3"
            return Response(b"out", status_code=200, headers=headers, media_type="image/jpeg")
        return Response(status_code=self.status, headers=headers)

    def request_ids(self):
        return [headers[protocol.REQUEST_ID] for headers, _ in self.calls]


class TwoWorkers(httpx.AsyncBaseTransport):
    """Sends http://w1/... to one fake worker and http://w2/... to the other."""

    def __init__(self, w1, w2):
        self.workers = {"w1": w1, "w2": w2}
        self.transports = {name: httpx.ASGITransport(app=w.app) for name, w in self.workers.items()}

    async def handle_async_request(self, request):
        name = request.url.host
        if self.workers[name].refuse_connections:
            raise httpx.ConnectError("connection refused", request=request)
        return await self.transports[name].handle_async_request(request)


@asynccontextmanager
async def started(w1, w2, rule="rr", config=None, scenario=1, **kwargs):
    """Run the dispatcher in process in front of two fake workers."""
    app = create_app(
        config or make_config(), rule=rule, scenario=scenario, rate=2.0, run_id="test",
        transport=TwoWorkers(w1, w2), **kwargs,
    )
    with anyio.fail_after(10):
        async with app.router.lifespan_context(app):
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://dispatcher") as client:
                yield client


def post(client, request_id, body=b"jpeg bytes"):
    headers = {protocol.REQUEST_ID: request_id, protocol.IMAGE_ID: "medium-03", protocol.SIZE_CLASS: "medium"}
    return client.post("/process", content=body, headers=headers)


async def test_request_is_forwarded_and_the_worker_reply_comes_back():
    w1, w2 = FakeWorker(processing_ms="42.000"), FakeWorker()
    async with started(w1, w2) as client:
        reply = await post(client, "r1")

    assert reply.status_code == 200
    assert reply.content == b"out"
    assert reply.headers[protocol.OUTCOME] == protocol.SUCCESS
    assert reply.headers[protocol.CHOSEN_WORKER] == "w1"
    assert reply.headers[protocol.PROCESSING_MS] == "42.000"
    assert w1.request_ids() == ["r1"]
    assert w2.calls == []


async def test_worker_gets_the_budget_header_equal_to_d_and_the_request_headers():
    w1, w2 = FakeWorker(), FakeWorker()
    async with started(w1, w2) as client:
        await post(client, "r1", body=b"the image")

    (headers, body), = w1.calls
    assert headers[protocol.BUDGET_MS] == "300"
    assert headers[protocol.PROBE] == "0"
    assert headers[protocol.REQUEST_ID] == "r1"
    assert headers[protocol.IMAGE_ID] == "medium-03"
    assert headers[protocol.SIZE_CLASS] == "medium"
    assert body == b"the image"


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


async def flush(client, path):
    reply = await client.post("/admin/flush", json={"path": str(path)})
    assert reply.status_code == 200
    assert reply.json() == {"path": str(path), "rows": len(read_rows(path))}
    return read_rows(path)


async def wait_until(condition):
    with anyio.fail_after(5):
        while not condition():
            await asyncio.sleep(0.01)


def decision_state(row):
    return (row["request_id"], row["chosen_worker"], row["unfinished_w1"], row["unfinished_w2"],
            row["estimate_w1_ms"], row["estimate_w2_ms"])


async def test_each_request_gives_one_log_row_with_the_state_before_the_decision(tmp_path):
    w1, w2 = FakeWorker(processing_ms="100.000"), FakeWorker(processing_ms="300.000")
    async with started(w1, w2, config=make_config(timeout_ms=2000)) as client:
        await post(client, "r1")
        await post(client, "r2")
        w1.delay_s = 0.3
        r3 = asyncio.create_task(post(client, "r3"))
        await wait_until(lambda: len(w1.calls) == 2)  # r3 is now unfinished on w1
        await post(client, "r4")
        await r3
        rows = await flush(client, tmp_path / "dispatcher.csv")

    with open(tmp_path / "dispatcher.csv", newline="", encoding="utf-8") as f:
        assert tuple(next(csv.reader(f))) == DISPATCHER_LOG_COLUMNS
    # A row is written when its request ends, so r4 comes before r3.
    assert sorted(decision_state(r) for r in rows) == [
        ("r1", "w1", "0", "0", "", ""),
        ("r2", "w2", "0", "0", "100.000", ""),
        ("r3", "w1", "0", "0", "100.000", "300.000"),
        ("r4", "w2", "1", "0", "100.000", "300.000"),
    ]
    first = next(r for r in rows if r["request_id"] == "r1")
    assert (first["run_id"], first["rule"], first["scenario"], first["rate"]) == ("test", "rr", "1", "2.0")
    assert (first["image_id"], first["size_class"], first["probe"], first["warmup"]) == ("medium-03", "medium", "0", "0")
    assert (first["worker_processing_ms"], first["worker_status"], first["outcome"]) == ("100.000", "200", "success")
    assert int(first["select_ns"]) > 0
    assert float(first["dispatcher_ms"]) > 0


def worker_that(behaviour):
    if behaviour == "succeeds":
        return FakeWorker()
    if behaviour == "is full":
        return FakeWorker(status=503, outcome=protocol.REJECTED)
    if behaviour == "expires the request":
        return FakeWorker(status=504, outcome=protocol.EXPIRED)
    if behaviour == "fails":
        return FakeWorker(status=500, outcome=protocol.ERROR)
    if behaviour == "refuses connections":
        worker = FakeWorker()
        worker.refuse_connections = True
        return worker
    if behaviour == "is slower than d":
        return FakeWorker(delay_s=1.0)
    raise ValueError(behaviour)


@pytest.mark.parametrize("behaviour, status, outcome, worker_status", [
    ("succeeds", 200, "success", "200"),
    ("is full", 503, "rejected", "503"),
    ("expires the request", 504, "expired", "504"),
    ("fails", 502, "error", "500"),
    ("refuses connections", 502, "error", ""),
    ("is slower than d", 504, "timeout", ""),
])
async def test_outcome_is_passed_back_and_the_unfinished_count_returns_to_0(
        tmp_path, behaviour, status, outcome, worker_status):
    w1, w2 = worker_that(behaviour), worker_that(behaviour)
    async with started(w1, w2) as client:
        reply = await post(client, "r1")
        await post(client, "r2")
        rows = await flush(client, tmp_path / "dispatcher.csv")

    assert reply.status_code == status
    assert reply.headers[protocol.OUTCOME] == outcome
    assert reply.headers[protocol.CHOSEN_WORKER] == "w1"
    r1, r2 = rows
    assert (r1["outcome"], r1["worker_status"]) == (outcome, worker_status)
    # r2's row holds the counts seen when r2 was assigned, after r1 ended.
    assert (r2["unfinished_w1"], r2["unfinished_w2"]) == ("0", "0")


async def test_a_failed_request_is_not_retried():
    w1, w2 = worker_that("fails"), worker_that("is slower than d")
    async with started(w1, w2) as client:
        replies = [await post(client, f"r{i}") for i in range(1, 5)]

    assert [r.status_code for r in replies] == [502, 504, 502, 504]
    assert w1.request_ids() == ["r1", "r3"]
    assert w2.request_ids() == ["r2", "r4"]
