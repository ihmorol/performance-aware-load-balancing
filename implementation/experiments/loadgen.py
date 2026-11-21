"""Open-loop load generator.

Every planned request gets its own asyncio task, which sleeps until the
planned time and then sends, whether or not earlier replies have arrived.
Response time is counted from the planned send time, not the actual one.

    python -m experiments.loadgen --config config/dev.toml \\
        --target http://127.0.0.1:8100/process --scenario 2 --rate 2 --round 1 \\
        --rule rr --run-id manual --out local/run-manual

The run folder gets schedule.csv (written before sending), generator.csv
(one row per request), and loadgen.json (the run parameters the summary needs).
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import time
from collections import Counter
from pathlib import Path

import httpx

from experiments.schedule import PlannedRequest, build_schedule, schedule_seed, write_schedule_csv
from plb import protocol
from plb.config import load_config
from plb.images import generate_image_set
from plb.rows import GENERATOR_LOG_COLUMNS

# With spin-wait on, the sender sleeps until this long before the planned
# time and then busy-waits.
SPIN_MARGIN_S = 0.020

OUTCOMES = (protocol.SUCCESS, protocol.REJECTED, protocol.EXPIRED, protocol.TIMEOUT, protocol.ERROR)

# Config values every run needs. The mix is only needed in scenarios 2 and 3.
NEEDED_KEYS = (
    "generator.timeout_ms", "generator.spin_wait",
    "run.length_s", "run.dropped_window_s", "run.achieved_rate_tolerance",
    "images.per_class", "images.resolutions.small", "images.resolutions.medium",
    "images.resolutions.large", "seeds.image_set", "seeds.schedule",
)
MIX_KEYS = ("images.mix.small", "images.mix.medium", "images.mix.large")


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


def write_generator_log(rows: list[dict], path: str | Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=GENERATOR_LOG_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _config_value(config: object, key: str) -> object:
    value = config
    for part in key.split("."):
        value = getattr(value, part)
    return value


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Send one run's seeded open-loop schedule.")
    parser.add_argument("--config", required=True, help="config TOML file")
    parser.add_argument("--target", required=True, help="URL to POST to, such as http://127.0.0.1:8100/process")
    parser.add_argument("--scenario", type=int, required=True, choices=(1, 2, 3))
    parser.add_argument("--rate", type=float, required=True, help="requests per second")
    parser.add_argument("--round", type=int, required=True)
    parser.add_argument("--rule", required=True, help="the rule under test; recorded only")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--out", required=True, help="run folder")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    needed = NEEDED_KEYS + (MIX_KEYS if args.scenario != 1 else ())
    unset = [key for key in needed if _config_value(config, key) is None]
    if unset:
        parser.error(f"unset in the config: {', '.join(unset)}")

    seed = schedule_seed(config.seeds.schedule, args.scenario, args.rate, args.round)
    schedule = build_schedule(seed, args.scenario, args.rate, config.run.length_s, config.images)
    out = Path(args.out)
    write_schedule_csv(schedule, out / "schedule.csv")
    run_info = {
        "run_id": args.run_id,
        "rule": args.rule,
        "scenario": args.scenario,
        "rate": args.rate,
        "round": args.round,
        "target": args.target,
        "length_s": config.run.length_s,
        "dropped_window_s": config.run.dropped_window_s,
        "achieved_rate_tolerance": config.run.achieved_rate_tolerance,
        "schedule_seed": seed,
    }
    (out / "loadgen.json").write_text(json.dumps(run_info, indent=2) + "\n", encoding="utf-8")

    bodies = {image.image_id: image.data for image in generate_image_set(config.images, config.seeds.image_set)}
    rows = asyncio.run(send_schedule(args.target, args.run_id, schedule, bodies,
                                     config.generator.timeout_ms / 1000, config.generator.spin_wait))
    write_generator_log(rows, out / "generator.csv")

    counts = Counter(row["outcome"] for row in rows)
    print(f"sent {len(rows)} requests to {args.target}: "
          + ", ".join(f"{outcome} {counts[outcome]}" for outcome in OUTCOMES))


if __name__ == "__main__":
    main()
