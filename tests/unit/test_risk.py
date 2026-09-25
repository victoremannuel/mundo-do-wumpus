from wumpus.agent.knowledge import KnowledgeBase
from wumpus.agent.risk import (
    CONFIRMED_DANGER,
    HAZARD_RISK_WEIGHTS,
    RISK_THRESHOLD,
    cell_risk,
    least_risk_candidate,
)
from wumpus.domain import EntityType, Position


def test_cell_risk_is_zero_for_a_proven_safe_cell() -> None:
    knowledge = KnowledgeBase(3, 3)
    knowledge.mark_visited(Position(1, 1))
    knowledge.mark_safe(Position(1, 1))

    assert cell_risk(knowledge, Position(1, 1)) == 0.0


def test_cell_risk_is_zero_for_an_unclassified_cell() -> None:
    knowledge = KnowledgeBase(3, 3)

    assert cell_risk(knowledge, Position(2, 2)) == 0.0


def test_cell_risk_is_confirmed_danger_for_a_confirmed_pit() -> None:
    knowledge = KnowledgeBase(3, 3)
    knowledge.mark_confirmed(Position(1, 2), EntityType.PIT)

    assert cell_risk(knowledge, Position(1, 2)) == CONFIRMED_DANGER


def test_cell_risk_is_confirmed_danger_for_a_confirmed_wumpus() -> None:
    knowledge = KnowledgeBase(3, 3)
    knowledge.mark_confirmed(Position(1, 2), EntityType.WUMPUS)

    assert cell_risk(knowledge, Position(1, 2)) == CONFIRMED_DANGER


def test_cell_risk_sums_every_surviving_hazard_candidate() -> None:
    knowledge = KnowledgeBase(3, 3)
    knowledge.mark_possible(Position(1, 2), EntityType.PIT)
    knowledge.mark_possible(Position(1, 2), EntityType.BAT)

    assert cell_risk(knowledge, Position(1, 2)) == (
        HAZARD_RISK_WEIGHTS[EntityType.PIT] + HAZARD_RISK_WEIGHTS[EntityType.BAT]
    )


def test_cell_risk_counts_a_confirmed_bat_the_same_as_a_possible_one() -> None:
    knowledge = KnowledgeBase(3, 3)
    knowledge.mark_confirmed(Position(1, 2), EntityType.BAT)

    assert cell_risk(knowledge, Position(1, 2)) == HAZARD_RISK_WEIGHTS[EntityType.BAT]


def test_cell_risk_ignores_a_hazard_type_already_ruled_out() -> None:
    knowledge = KnowledgeBase(3, 3)
    knowledge.mark_possible(Position(1, 2), EntityType.PIT)
    knowledge.mark_not(Position(1, 2), EntityType.PIT)

    assert cell_risk(knowledge, Position(1, 2)) == 0.0


def test_least_risk_candidate_is_none_without_any_scored_neighbor() -> None:
    knowledge = KnowledgeBase(3, 3)
    knowledge.mark_visited(Position(1, 1))
    knowledge.mark_safe(Position(1, 1))

    assert least_risk_candidate(knowledge, Position(1, 1)) is None


def test_least_risk_candidate_ignores_cells_outside_the_reachable_safe_region() -> None:
    knowledge = KnowledgeBase(5, 5)
    knowledge.mark_visited(Position(1, 1))
    knowledge.mark_safe(Position(1, 1))
    knowledge.mark_possible(Position(5, 5), EntityType.BAT)

    assert least_risk_candidate(knowledge, Position(1, 1)) is None


def test_least_risk_candidate_picks_the_lowest_score() -> None:
    knowledge = KnowledgeBase(3, 3)
    knowledge.mark_visited(Position(1, 1))
    knowledge.mark_safe(Position(1, 1))
    knowledge.mark_possible(Position(2, 1), EntityType.PIT)
    knowledge.mark_possible(Position(1, 2), EntityType.BAT)

    candidate = least_risk_candidate(knowledge, Position(1, 1))

    assert candidate is not None
    assert candidate.position == Position(1, 2)
    assert candidate.score == HAZARD_RISK_WEIGHTS[EntityType.BAT]


def test_least_risk_candidate_never_returns_a_confirmed_danger_cell() -> None:
    knowledge = KnowledgeBase(3, 1)
    knowledge.mark_visited(Position(1, 1))
    knowledge.mark_safe(Position(1, 1))
    knowledge.mark_confirmed(Position(2, 1), EntityType.PIT)

    assert least_risk_candidate(knowledge, Position(1, 1)) is None


def test_least_risk_candidate_reaches_through_a_connected_safe_region() -> None:
    knowledge = KnowledgeBase(4, 1)
    knowledge.mark_visited(Position(1, 1))
    knowledge.mark_safe(Position(1, 1))
    knowledge.mark_visited(Position(2, 1))
    knowledge.mark_safe(Position(2, 1))
    knowledge.mark_possible(Position(3, 1), EntityType.WUMPUS)

    candidate = least_risk_candidate(knowledge, Position(1, 1))

    assert candidate is not None
    assert candidate.position == Position(3, 1)


def test_risk_threshold_equals_the_wumpus_weight() -> None:
    assert RISK_THRESHOLD == HAZARD_RISK_WEIGHTS[EntityType.WUMPUS]
