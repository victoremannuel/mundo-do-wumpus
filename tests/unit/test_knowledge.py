import pytest

from wumpus.agent import AgentMemory, KnowledgeBase, KnowledgeConflictError
from wumpus.domain import (
    Action,
    ActionResult,
    AgentObservation,
    Direction,
    EntityType,
    Perception,
    Position,
)


NO_PERCEPTION = Perception(
    stench=False,
    breeze=False,
    bat_noise=False,
    glitter=False,
    bump=False,
    scream=False,
)


def knowledge() -> KnowledgeBase:
    return KnowledgeBase(rows=6, cols=6)


def test_knowledge_starts_with_every_cell_unknown() -> None:
    base = knowledge()

    assert len(base.all_cells) == 36
    assert base.unknown == base.all_cells
    assert base.visited == frozenset()
    assert base.safe == frozenset()
    assert base.frontier == frozenset()
    assert base.revision == 0


def test_visited_cells_create_an_in_bounds_exploration_frontier() -> None:
    base = knowledge()

    assert base.mark_visited(Position(1, 1)) is True

    assert base.visited == frozenset({Position(1, 1)})
    assert base.frontier == frozenset({Position(1, 2), Position(2, 1)})
    assert base.cell(Position(1, 1)).visited is True


def test_safe_cells_have_explicit_negative_knowledge_for_every_hazard() -> None:
    base = knowledge()
    position = Position(2, 2)

    base.mark_possible(position, EntityType.PIT)
    assert base.mark_safe(position) is True

    cell = base.cell(position)
    assert cell.safe is True
    assert cell.not_pit is True
    assert cell.not_wumpus is True
    assert cell.not_bat is True
    assert position not in base.possible_pits
    assert position not in base.unknown


def test_possible_hazards_remain_separated_by_type() -> None:
    base = knowledge()
    pit = Position(2, 2)
    wumpus = Position(3, 3)
    bat = Position(4, 4)

    base.mark_possible(pit, EntityType.PIT)
    base.mark_possible(wumpus, EntityType.WUMPUS)
    base.mark_possible(bat, EntityType.BAT)

    assert base.possible_pits == frozenset({pit})
    assert base.possible_wumpus == frozenset({wumpus})
    assert base.possible_bats == frozenset({bat})
    assert {pit, wumpus, bat}.isdisjoint(base.unknown)


def test_negative_knowledge_removes_a_candidate_and_only_becomes_safe_when_complete() -> None:
    base = knowledge()
    position = Position(2, 3)
    base.mark_possible(position, EntityType.PIT)

    base.mark_not(position, EntityType.PIT)

    assert position in base.not_pit
    assert position not in base.possible_pits
    assert position in base.unknown
    assert position not in base.safe

    base.mark_not(position, EntityType.WUMPUS)
    base.mark_not(position, EntityType.BAT)

    assert position in base.safe
    assert position not in base.unknown


def test_confirming_a_hazard_is_monotonic_and_rules_out_other_types() -> None:
    base = knowledge()
    position = Position(5, 5)
    base.mark_possible(position, EntityType.WUMPUS)

    assert base.mark_confirmed(position, EntityType.WUMPUS) is True

    cell = base.cell(position)
    assert cell.confirmed_wumpus is True
    assert cell.possible_wumpus is False
    assert cell.not_pit is True
    assert cell.not_bat is True
    assert position in base.confirmed_wumpus
    assert position not in base.unknown


def test_confirmed_bats_remain_classified_as_hazards() -> None:
    base = knowledge()
    position = Position(6, 6)

    base.mark_confirmed(position, EntityType.BAT)

    assert base.cell(position).confirmed_bat is True
    assert position in base.confirmed_bats
    assert position not in base.safe


def test_confirmed_wumpus_can_transition_to_dead_and_safe() -> None:
    base = knowledge()
    position = Position(4, 5)
    base.mark_confirmed(position, EntityType.WUMPUS)
    revision_before_death = base.revision

    assert base.mark_wumpus_dead(position) is True

    cell = base.cell(position)
    assert cell.confirmed_wumpus is False
    assert cell.dead_wumpus is True
    assert cell.not_wumpus is True
    assert cell.not_pit is True
    assert cell.not_bat is True
    assert cell.safe is True
    assert position not in base.confirmed_wumpus
    assert position in base.dead_wumpus
    assert base.revision == revision_before_death + 1
    assert base.mark_wumpus_dead(position) is False
    assert base.revision == revision_before_death + 1


def test_only_a_confirmed_wumpus_can_transition_to_dead() -> None:
    base = knowledge()
    position = Position(4, 5)

    with pytest.raises(KnowledgeConflictError):
        base.mark_wumpus_dead(position)

    base.mark_possible(position, EntityType.WUMPUS)
    with pytest.raises(KnowledgeConflictError):
        base.mark_wumpus_dead(position)


def test_contradictory_classifications_fail_closed() -> None:
    base = knowledge()
    safe_position = Position(2, 2)
    pit_position = Position(3, 3)
    base.mark_safe(safe_position)
    base.mark_confirmed(pit_position, EntityType.PIT)

    with pytest.raises(KnowledgeConflictError):
        base.mark_possible(safe_position, EntityType.PIT)
    with pytest.raises(KnowledgeConflictError):
        base.mark_not(pit_position, EntityType.PIT)
    with pytest.raises(KnowledgeConflictError):
        base.mark_confirmed(pit_position, EntityType.WUMPUS)
    with pytest.raises(KnowledgeConflictError):
        base.mark_safe(pit_position)


def test_revision_changes_once_per_new_logical_update_and_not_for_repetition() -> None:
    base = knowledge()
    position = Position(2, 2)

    assert base.mark_visited(position) is True
    assert base.revision == 1
    assert base.mark_visited(position) is False
    assert base.revision == 1
    assert base.mark_possible(position, EntityType.PIT) is True
    assert base.revision == 2
    assert base.mark_confirmed(position, EntityType.PIT) is True
    assert base.revision == 3
    assert base.mark_confirmed(position, EntityType.PIT) is False
    assert base.revision == 3


def test_invalid_dimensions_positions_and_non_hazards_are_rejected() -> None:
    with pytest.raises(ValueError):
        KnowledgeBase(rows=0, cols=6)

    base = knowledge()
    with pytest.raises(ValueError):
        base.mark_visited(Position(7, 1))
    with pytest.raises(ValueError):
        base.mark_possible(Position(2, 2), EntityType.GOLD)


def test_memory_records_direct_safe_visits_without_running_sensor_inference() -> None:
    base = knowledge()
    memory = AgentMemory(Position(1, 1), Direction.NORTH, base)
    breeze = Perception(**{**vars(NO_PERCEPTION), "breeze": True})

    memory.record_observation(
        AgentObservation(
            position=Position(2, 1),
            direction=Direction.NORTH,
            perception=breeze,
            score=-1,
            collected_gold=0,
            active=True,
        )
    )

    assert base.visited == frozenset({Position(1, 1), Position(2, 1)})
    assert {Position(1, 1), Position(2, 1)}.issubset(base.safe)
    assert Position(3, 1) not in base.not_pit
    assert Position(2, 2) not in base.not_pit


def test_a_lethal_destination_is_visited_but_not_marked_safe() -> None:
    base = knowledge()
    memory = AgentMemory(Position(1, 1), Direction.NORTH, base)
    destination = Position(2, 1)

    memory.record_result(
        ActionResult(
            action=Action.MOVE_FORWARD,
            position=destination,
            direction=Direction.NORTH,
            score_delta=-1001,
            total_score=-1001,
            perception=NO_PERCEPTION,
            died=True,
        )
    )

    assert destination in base.visited
    assert destination not in base.safe
    assert destination in base.unknown
