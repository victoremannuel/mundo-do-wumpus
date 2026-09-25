import pytest

from wumpus.agent import (
    GOLD_RISK_THRESHOLD,
    NO_GOLD_RISK_THRESHOLD,
    estimate_exploration_utility,
    risk_threshold,
    should_explore,
)


def test_risk_tolerance_is_lower_after_collecting_gold() -> None:
    assert risk_threshold(0) == NO_GOLD_RISK_THRESHOLD
    assert risk_threshold(1) == GOLD_RISK_THRESHOLD
    assert GOLD_RISK_THRESHOLD < NO_GOLD_RISK_THRESHOLD


def test_same_pit_risk_is_accepted_before_gold_and_rejected_after_gold() -> None:
    assert should_explore(
        candidate_risk=3.0,
        movement_actions=1,
        collected_gold=0,
        total_gold=3,
    )
    assert not should_explore(
        candidate_risk=3.0,
        movement_actions=1,
        collected_gold=1,
        total_gold=3,
    )


def test_utility_subtracts_movement_hazard_and_arrow_costs() -> None:
    without_arrow = estimate_exploration_utility(
        candidate_risk=2.0,
        movement_actions=3,
        collected_gold=0,
        total_gold=3,
    )
    with_arrow = estimate_exploration_utility(
        candidate_risk=2.0,
        movement_actions=3,
        collected_gold=0,
        total_gold=3,
        requires_arrow=True,
    )

    assert without_arrow.expected_gold_value == 1000
    assert without_arrow.movement_cost == 3
    assert without_arrow.estimated_hazard_cost == 500
    assert without_arrow.arrow_cost == 0
    assert with_arrow.arrow_cost == 10
    assert with_arrow.total == without_arrow.total - 10


def test_reachable_bat_risk_is_abandoned_after_two_gold_on_utility() -> None:
    assert not should_explore(
        candidate_risk=2.0,
        movement_actions=1,
        collected_gold=2,
        total_gold=3,
    )


def test_expected_gold_value_is_zero_when_configured_supply_is_exhausted() -> None:
    estimate = estimate_exploration_utility(
        candidate_risk=0.0,
        movement_actions=1,
        collected_gold=3,
        total_gold=3,
    )

    assert estimate.expected_gold_value == 0
    assert estimate.total < 0


@pytest.mark.parametrize(
    ("candidate_risk", "movement_actions", "collected_gold", "total_gold"),
    [
        (-1.0, 1, 0, 3),
        (1.0, -1, 0, 3),
        (1.0, 1, -1, 3),
        (1.0, 1, 0, -1),
    ],
)
def test_utility_rejects_invalid_inputs(
    candidate_risk: float,
    movement_actions: int,
    collected_gold: int,
    total_gold: int,
) -> None:
    with pytest.raises(ValueError):
        estimate_exploration_utility(
            candidate_risk=candidate_risk,
            movement_actions=movement_actions,
            collected_gold=collected_gold,
            total_gold=total_gold,
        )
