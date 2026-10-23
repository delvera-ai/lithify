from lithify.config import Schedule
from lithify.state import State, choose_k, phase_for, stability

S = Schedule(window=10)


def hist(fp: list[bool], churn: int = 0) -> list[dict]:
    return [{"first_pass": f, "churn_lines": churn} for f in fp]


def test_empty_history_is_zero():
    assert stability([], S) == 0.0


def test_never_passing_is_zero_even_without_churn():
    assert stability(hist([False] * 10, churn=0), S) == 0.0


def test_all_passing_no_churn_is_one():
    assert stability(hist([True] * 10), S) == 1.0


def test_churn_lowers_stability():
    calm = stability(hist([True] * 10, churn=0), S)
    busy = stability(hist([True] * 10, churn=80), S)
    assert busy < calm
    assert busy == 0.7  # churn saturates; first-pass weight remains


def test_few_tasks_are_discounted():
    assert stability(hist([True]), S) < stability(hist([True] * 5), S)


def test_window_only_counts_recent():
    old_fail_new_pass = hist([False] * 20 + [True] * 10)
    assert stability(old_fail_new_pass, S) == 1.0


def test_phases():
    assert phase_for(0.1, S) == "genesis"
    assert phase_for(0.5, S) == "build"
    assert phase_for(0.9, S) == "cruise"


def test_choose_k_by_phase():
    assert choose_k(State(), S, 3)[0] == 3
    assert choose_k(State(history=hist([True] * 10)), S, 3)[0] == 0
    mid = State(history=hist([True] * 6 + [False] * 4))
    assert choose_k(mid, S, 3)[0] == 1


def test_anomaly_spikes():
    cruising = hist([True] * 10)
    assert choose_k(State(consecutive_failures=1, history=cruising), S, 3)[0] == 1
    assert choose_k(State(consecutive_failures=2, history=cruising), S, 3)[0] == 3
