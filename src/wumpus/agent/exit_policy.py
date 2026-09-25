"""Rational exploration-abandonment policy based on agent-owned facts.

The heuristic implements plan sections 45-48.  It compares the incremental
utility of one least-risk exploration target with abandoning that target:
expected gold value minus estimated movement, hazard, and optional arrow
costs.  The current score is intentionally absent because it is shared by
both alternatives and therefore cancels from the comparison.
"""

from __future__ import annotations

from dataclasses import dataclass

from wumpus.agent.risk import HAZARD_RISK_WEIGHTS, RISK_THRESHOLD
from wumpus.domain import Action, EntityType
from wumpus.game.scoring import DEATH_PENALTY, GOLD_REWARD, action_cost


NO_GOLD_RISK_THRESHOLD = RISK_THRESHOLD
GOLD_RISK_THRESHOLD = float(HAZARD_RISK_WEIGHTS[EntityType.BAT])


@dataclass(frozen=True)
class UtilityEstimate:
    """Auditable components of one exploration utility estimate."""

    expected_gold_value: float
    movement_cost: float
    estimated_hazard_cost: float
    arrow_cost: float

    @property
    def total(self) -> float:
        return (
            self.expected_gold_value
            - self.movement_cost
            - self.estimated_hazard_cost
            - self.arrow_cost
        )


def risk_threshold(collected_gold: int) -> float:
    """Accept strictly less danger after obtaining any gold."""

    return GOLD_RISK_THRESHOLD if collected_gold > 0 else NO_GOLD_RISK_THRESHOLD


def estimate_exploration_utility(
    *,
    candidate_risk: float,
    movement_actions: int,
    collected_gold: int,
    total_gold: int,
    requires_arrow: bool = False,
) -> UtilityEstimate:
    """Estimate incremental utility without consulting hidden world state.

    Risk weights are converted into a conservative fraction of the canonical
    death penalty.  Each already-collected gold discounts the benefit of
    searching for another, expressing section 48's growing preference for
    preserving the score already earned.
    """

    if candidate_risk < 0:
        raise ValueError("candidate_risk cannot be negative")
    if movement_actions < 0:
        raise ValueError("movement_actions cannot be negative")
    if collected_gold < 0:
        raise ValueError("collected_gold cannot be negative")
    if total_gold < 0:
        raise ValueError("total_gold cannot be negative")

    remaining_gold = max(total_gold - collected_gold, 0)
    expected_gold_value = (
        GOLD_REWARD * remaining_gold / total_gold if total_gold else 0.0
    )

    return UtilityEstimate(
        expected_gold_value=expected_gold_value,
        movement_cost=movement_actions * abs(action_cost(Action.MOVE_FORWARD)),
        estimated_hazard_cost=(
            candidate_risk / NO_GOLD_RISK_THRESHOLD * abs(DEATH_PENALTY)
        ),
        arrow_cost=abs(action_cost(Action.SHOOT)) if requires_arrow else 0.0,
    )


def should_explore(
    *,
    candidate_risk: float,
    movement_actions: int,
    collected_gold: int,
    total_gold: int,
    requires_arrow: bool = False,
) -> bool:
    """Return whether the least-risk alternative is rationally acceptable."""

    if candidate_risk > risk_threshold(collected_gold):
        return False
    return (
        estimate_exploration_utility(
            candidate_risk=candidate_risk,
            movement_actions=movement_actions,
            collected_gold=collected_gold,
            total_gold=total_gold,
            requires_arrow=requires_arrow,
        ).total
        > 0.0
    )
