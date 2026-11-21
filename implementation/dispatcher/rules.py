"""The four routing rules as pure functions, plus the EWMA update.

select() takes a snapshot of the two workers and the rule state, and returns
the index of the chosen worker (0 is w1, 1 is w2) and the new rule state. It
does no I/O and reads no clock, so the tests can call it directly.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

RULES = ("rr", "wrr", "lur", "feedback")


@dataclass(frozen=True)
class WorkerView:
    """What select() sees of one worker at decision time."""
    unfinished: int
    estimate_ms: float | None  # None until the worker's first sample


@dataclass(frozen=True)
class RuleState:
    # Index chosen by the previous select() call, None before the first one.
    last_pick: int | None = None
    # Weighted round-robin only: the integer weights from the config and
    # each worker's current value.
    weights: tuple[int, int] | None = None
    currents: tuple[int, int] = (0, 0)


def select(rule: str, workers: tuple[WorkerView, WorkerView], state: RuleState) -> tuple[int, RuleState]:
    """Pick a worker by the named rule."""
    if rule == "rr":
        return _lower((0, 0), state)
    if rule == "wrr":
        return _smooth_weighted(state)
    if rule == "lur":
        return _lower((workers[0].unfinished, workers[1].unfinished), state)
    if rule == "feedback":
        return _lower((_feedback_score(workers[0]), _feedback_score(workers[1])), state)
    raise ValueError(f"unknown rule {rule!r}")


def _smooth_weighted(state: RuleState) -> tuple[int, RuleState]:
    """Smooth weighted round-robin.

    Add each worker's weight to its current value, pick the larger current
    value, and subtract the total weight from the chosen one.
    """
    w1, w2 = state.weights
    currents = (state.currents[0] + w1, state.currents[1] + w2)
    # The larger current value wins, so _lower gets them negated.
    chosen, state = _lower((-currents[0], -currents[1]), state)
    if chosen == 0:
        currents = (currents[0] - (w1 + w2), currents[1])
    else:
        currents = (currents[0], currents[1] - (w1 + w2))
    return chosen, replace(state, currents=currents)


def _feedback_score(worker: WorkerView) -> float:
    """(unfinished + 1) x estimate. A worker with no estimate yet scores 0."""
    if worker.estimate_ms is None:
        return 0.0
    return (worker.unfinished + 1) * worker.estimate_ms


def update_estimate(old_ms: float | None, new_ms: float, a: float) -> float:
    """EWMA: estimate = (1 - a) x estimate + a x newest processing time.

    A worker's first sample sets its estimate directly. Starting from zero
    would leave the estimate far too low after a short warm-up.
    """
    if old_ms is None:
        return new_ms
    return (1 - a) * old_ms + a * new_ms


def _lower(scores: tuple[float, float], state: RuleState) -> tuple[int, RuleState]:
    """Pick the worker with the lower score.

    On a tie, pick the worker that was not picked last time (w1 if nothing
    was picked yet). The spec's one shared tie counter is kept as this one
    shared value. A counter that only counted ties would break 1:1 weighted
    round-robin: with currents starting at 0, every odd pick is a tie, and
    the picks would come out w1, w2, w2, w1. Round-robin is the case where
    every pick is a tie.
    """
    if scores[0] < scores[1]:
        chosen = 0
    elif scores[1] < scores[0]:
        chosen = 1
    elif state.last_pick is None:
        chosen = 0
    else:
        chosen = 1 - state.last_pick
    return chosen, replace(state, last_pick=chosen)
