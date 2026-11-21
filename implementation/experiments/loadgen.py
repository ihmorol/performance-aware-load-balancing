"""Open-loop load generator.

Every planned request gets its own asyncio task, which sleeps until the
planned time and then sends, whether or not earlier replies have arrived.
Response time is counted from the planned send time, not the actual one.
"""

from __future__ import annotations

import asyncio
import time

import httpx

from experiments.schedule import PlannedRequest
from plb import protocol

# With spin-wait on, the sender sleeps until this long before the planned
# time and then busy-waits.
SPIN_MARGIN_S = 0.020


async def send_schedule(target: str, run_id: str, schedule: list[PlannedRequest],
                        bodies: dict[str, bytes], timeout_s: float, spin_wait: bool) -> list[dict]:
    """Send every planned request to target and return one log row each, in schedule order."""
    # No connection limit, so a send never waits for a free connection.
    limits = httpx.Limits(max_connections=None, max_keepalive_connections=None)
    async with httpx.AsyncClient(limits=limits, timeout=timeout_s) as client:
        start = time.perf_counter()
        tasks = [
            asyncio.create_task(_send_one(client, target, run_id, planned, bodies, start, timeout_s,
                                          spin_wait))
            for planned in schedule
        ]
        return list(await asyncio.gather(*tasks))


async def _send_one(client: httpx.AsyncClient, target: str, run_id: str, planned: PlannedRequest,
                    bodies: dict[str, bytes], start: float, timeout_s: float,
                    spin_wait: bool) -> dict:
    planned_at = start + planned.planned_offset_s
    await _wait_until(planned_at, spin_wait)
    sent_at = time.perf_counter()
    headers = {
        protocol.REQUEST_ID: planned.request_id,
        protocol.IMAGE_ID: planned.image_id,
        protocol.SIZE_CLASS: planned.size_class,
    }
    status, outcome, reply_headers = "", protocol.TIMEOUT, {}
    try:
        # wait_for enforces the timeout even where an HTTPX transport ignores
        # the client's own timeout setting.
        reply = await asyncio.wait_for(
            client.post(target, content=bodies[planned.image_id], headers=headers), timeout_s)
        status, outcome, reply_headers = str(reply.status_code), reply_outcome(reply), reply.headers
    except (TimeoutError, httpx.TimeoutException):
        pass
    except httpx.HTTPError:
        outcome = protocol.ERROR
    done_at = time.perf_counter()
    return {
        "run_id": run_id,
        "request_id": planned.request_id,
        "image_id": planned.image_id,
        "size_class": planned.size_class,
        "planned_offset_s": f"{planned.planned_offset_s:.6f}",
        "actual_offset_s": f"{sent_at - start:.6f}",
        "send_lag_ms": f"{(sent_at - planned_at) * 1000:.3f}",
        "status": status,
        "outcome": outcome,
        "response_ms": f"{(done_at - planned_at) * 1000:.3f}",
        # A worker answering directly sends no chosen worker header.
        "chosen_worker": reply_headers.get(protocol.CHOSEN_WORKER, ""),
        "processing_ms": reply_headers.get(protocol.PROCESSING_MS, ""),
        "output_bytes": reply_headers.get(protocol.OUTPUT_BYTES, ""),
    }


async def _wait_until(planned_at: float, spin_wait: bool) -> None:
    if not spin_wait:
        await asyncio.sleep(max(0.0, planned_at - time.perf_counter()))
        return
    await asyncio.sleep(max(0.0, planned_at - SPIN_MARGIN_S - time.perf_counter()))
    # The busy-wait blocks the event loop for up to SPIN_MARGIN_S, so other
    # tasks wait too. That is accepted: the pilot decides whether the switch
    # is used at all.
    while time.perf_counter() < planned_at:
        pass


def reply_outcome(reply: httpx.Response) -> str:
    """Terminal outcome of a reply from a worker or from the dispatcher."""
    if reply.status_code == 200:
        return protocol.SUCCESS
    if reply.status_code == 503:
        return protocol.REJECTED
    if reply.status_code == 504:
        # The worker's expired reply, passed on by the dispatcher, says so in
        # its outcome header. Any other 504 is the dispatcher's own timeout.
        if reply.headers.get(protocol.OUTCOME) == protocol.EXPIRED:
            return protocol.EXPIRED
        return protocol.TIMEOUT
    return protocol.ERROR
