"""Seeded request schedule for one run, and its CSV file.

The schedule is a list of planned requests: Poisson arrivals (exponential
gaps) at the run's rate over the run length, each with an image chosen from
the scenario's mix. The seed depends on the base seed, scenario, rate, and
round, never on the rule, so every rule in one round, scenario, and rate gets
the same schedule.
"""

from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from pathlib import Path

from plb.config import ImagesConfig
from plb.images import SIZE_CLASSES

SCHEDULE_COLUMNS = ("request_id", "planned_offset_s", "image_id", "size_class")


@dataclass(frozen=True)
class PlannedRequest:
    request_id: str
    planned_offset_s: float  # seconds after the run's start
    image_id: str
    size_class: str


def schedule_seed(base_seed: int, scenario: int, rate: float, round_number: int) -> str:
    """The seed string for one scenario, rate, and round.

    float(rate) makes 2 and 2.0 the same seed.
    """
    return f"{base_seed}:{scenario}:{float(rate)!r}:{round_number}"


def build_schedule(seed: str, scenario: int, rate: float, length_s: float,
                   images: ImagesConfig) -> list[PlannedRequest]:
    """Plan every request whose offset falls before length_s."""
    # A string seed is hashed with SHA-512, so it gives the same stream on
    # every machine and every run.
    rng = random.Random(seed)
    schedule = []
    offset = 0.0
    while True:
        # The draws always come in this order: gap, size class, image index.
        offset += rng.expovariate(rate)
        if offset >= length_s:
            return schedule
        size_class = _size_class(rng, scenario, images)
        index = rng.randrange(images.per_class)
        schedule.append(PlannedRequest(
            request_id=f"r{len(schedule):05d}",
            planned_offset_s=offset,
            image_id=f"{size_class}-{index:02d}",
            size_class=size_class,
        ))


def _size_class(rng: random.Random, scenario: int, images: ImagesConfig) -> str:
    # Scenario 1 uses only the medium class.
    if scenario == 1:
        return "medium"
    mix = images.mix
    return rng.choices(SIZE_CLASSES, weights=(mix.small, mix.medium, mix.large))[0]


def write_schedule_csv(schedule: list[PlannedRequest], path: str | Path) -> None:
    """Write the schedule as CSV. The same schedule always gives the same bytes."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(SCHEDULE_COLUMNS)
        for planned in schedule:
            writer.writerow((planned.request_id, f"{planned.planned_offset_s:.6f}",
                             planned.image_id, planned.size_class))
