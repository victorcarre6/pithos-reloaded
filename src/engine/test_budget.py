import math

import pytest

from engine.budget import Budget, FINALIZATION_RESERVE_SECONDS


def test_one_anchor_and_reserve_close_admission():
    now = [100.0]
    budget = Budget(20.0, clock=lambda: now[0])
    assert budget.deadline == 120.0
    assert budget.can_start
    now[0] = 120.0 - FINALIZATION_RESERVE_SECONDS
    assert not budget.can_start
    assert budget.spendable == 0
    assert budget.remaining == FINALIZATION_RESERVE_SECONDS
    now[0] = 121.0
    assert budget.remaining == 0
    assert budget.elapsed == 21.0
    assert budget.deadline == 120.0


def test_short_budget_is_entirely_reserved():
    budget = Budget(0.001, clock=lambda: 0.0)
    assert not budget.can_start
    assert budget.spendable == 0
    assert budget.remaining == 0.001


@pytest.mark.parametrize("seconds", [0, -1, math.nan, math.inf, -math.inf, True])
def test_invalid_budget_is_rejected(seconds):
    with pytest.raises(ValueError):
        Budget(seconds)
