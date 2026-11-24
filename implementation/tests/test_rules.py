import pytest

from dispatcher.rules import RULES, RuleState, WorkerView, select, update_estimate

IDLE = (WorkerView(unfinished=0, estimate_ms=None), WorkerView(unfinished=0, estimate_ms=None))


def picks(rule, workers, state, count):
    """Run select() count times on the same snapshot; return the chosen indexes."""
    chosen = []
    for _ in range(count):
        index, state = select(rule, workers, state)
        chosen.append(index)
    return chosen


def test_round_robin_select_alternates_over_100_picks():
    assert picks("rr", IDLE, RuleState(), 100) == [0, 1] * 50


# Defense guide 7.4 Example A: A has 2 unfinished at 100 ms, B has 0 at 500 ms.
EXAMPLE_A = (WorkerView(unfinished=2, estimate_ms=100.0), WorkerView(unfinished=0, estimate_ms=500.0))


def test_least_unfinished_requests_rule_picks_idle_slow_worker_in_example_a():
    chosen, _ = select("lur", EXAMPLE_A, RuleState())
    assert chosen == 1  # B


def test_feedback_picks_busy_fast_worker_in_example_a():
    chosen, _ = select("feedback", EXAMPLE_A, RuleState())
    assert chosen == 0  # A: 300 ms against 500 ms


def test_feedback_picks_idle_slow_worker_in_example_b():
    # Example B: A has 9 unfinished at 100 ms, B has 0 at 500 ms.
    workers = (WorkerView(unfinished=9, estimate_ms=100.0), WorkerView(unfinished=0, estimate_ms=500.0))
    chosen, _ = select("feedback", workers, RuleState())
    assert chosen == 1  # B: 500 ms against 1,000 ms


def test_feedback_picks_like_least_unfinished_requests_rule_in_example_c():
    # Example C: equal estimates, so only the unfinished counts differ.
    workers = (WorkerView(unfinished=3, estimate_ms=200.0), WorkerView(unfinished=1, estimate_ms=200.0))
    feedback, _ = select("feedback", workers, RuleState())
    least_unfinished_requests, _ = select("lur", workers, RuleState())
    assert feedback == least_unfinished_requests == 1


def test_weighted_round_robin_select_with_3_to_1_gives_3_and_1_in_every_block_of_4():
    chosen = picks("wrr", IDLE, RuleState(weights=(3, 1)), 400)
    blocks = [chosen[i:i + 4] for i in range(0, 400, 4)]
    assert all(block.count(0) == 3 and block.count(1) == 1 for block in blocks)


def test_weighted_round_robin_select_spreads_the_slow_worker_inside_the_cycle():
    # By hand, currents start at (0, 0): pick 1 (3, 1) -> w1, pick 2 (2, 2)
    # tie -> w2, pick 3 (5, -1) -> w1, pick 4 (4, 0) -> w1, back to (0, 0).
    assert picks("wrr", IDLE, RuleState(weights=(3, 1)), 8) == [0, 1, 0, 0, 0, 1, 0, 0]


def test_weighted_round_robin_select_with_1_to_1_alternates():
    assert picks("wrr", IDLE, RuleState(weights=(1, 1)), 100) == [0, 1] * 50


EQUAL = (WorkerView(unfinished=2, estimate_ms=150.0), WorkerView(unfinished=2, estimate_ms=150.0))


@pytest.mark.parametrize("rule", RULES)
def test_ties_alternate_under_every_rule(rule):
    # Every pick is a tie under rr, lur, and feedback; under wrr 1:1 the odd
    # picks are. The first tie goes to w1.
    assert picks(rule, EQUAL, RuleState(weights=(1, 1)), 10) == [0, 1] * 5


def test_feedback_rule_ewma_update_gives_hand_computed_value():
    # 0.8 x 100 + 0.2 x 200 = 120
    assert update_estimate(100.0, 200.0, 0.2) == pytest.approx(120.0)


def test_feedback_rule_first_sample_sets_the_estimate():
    # Not 0.2 x 150 = 30, which is what starting from zero would give.
    assert update_estimate(None, 150.0, 0.2) == 150.0
