"""Regression coverage for bounded logical-agent cycle recovery."""

from collections import deque

from wumpus.agent import AgentMemory, KnowledgeBase, Strategy
from wumpus.agent.memory import StagnationEvent
from wumpus.domain import Action, ActionResult, Direction, Perception, Position


START = Position(1, 1)
TARGET = Position(1, 2)
ALTERNATIVE = Position(2, 1)


def result(action: Action) -> ActionResult:
    return ActionResult(
        action=action,
        position=START,
        direction=Direction.NORTH,
        score_delta=-1,
        total_score=-1,
        perception=Perception(False, False, False, False, False, False),
    )


def memory() -> AgentMemory:
    return AgentMemory(START, Direction.NORTH, KnowledgeBase(3, 3))


def rotation_event(actions: tuple[Action, ...]) -> StagnationEvent:
    agent_memory = memory()
    event = None
    for action in actions:
        agent_memory.begin_action(TARGET)
        agent_memory.record_result(result(action))
        event = agent_memory.finish_action(result(action))
    assert event is not None
    return event


def test_four_rotations_without_progress_emit_cycle_detected() -> None:
    event = rotation_event((Action.TURN_RIGHT,) * 4)

    assert event.position == START
    assert event.objective == TARGET
    assert event.rotations == 4
    assert event.turns_without_progress == 4


def test_a_legitimate_three_turn_right_left_turn_is_not_flagged_as_a_cycle() -> None:
    """A 90-degree left turn is three real TURN_RIGHT actions (no TURN_LEFT).

    Three consecutive rotations must stay below the stagnation threshold so a
    legitimate left-turn sequence is never misclassified as a loop.
    """

    agent_memory = memory()
    event = None
    for action in (Action.TURN_RIGHT,) * 3:
        agent_memory.begin_action(TARGET)
        agent_memory.record_result(result(action))
        event = agent_memory.finish_action(result(action))
    assert event is None


def test_repeated_right_rotations_are_detected() -> None:
    event = rotation_event((Action.TURN_RIGHT,) * 4)

    assert event.rotations == 4


def test_recovery_clears_plan_and_temporarily_blocks_its_target() -> None:
    strategy = Strategy()
    strategy._target = TARGET
    strategy._path = [START, TARGET]
    strategy._actions = deque((Action.TURN_RIGHT, Action.MOVE_FORWARD))
    event = rotation_event((Action.TURN_RIGHT,) * 4)

    strategy.recover_from_stagnation(event)

    assert strategy.planned_actions == ()
    assert (TARGET, event.knowledge_revision) in strategy.blocked_targets
    assert "CYCLE_DETECTED" in strategy.last_reason.reason  # type: ignore[union-attr]


def test_blocked_target_is_not_immediately_selected_and_revision_reenables_it() -> None:
    knowledge = KnowledgeBase(3, 3)
    for cell in (START, TARGET, ALTERNATIVE):
        knowledge.mark_safe(cell)
    knowledge.mark_visited(START)
    strategy = Strategy()
    event = StagnationEvent(START, TARGET, 4, 4, knowledge.revision)
    strategy.recover_from_stagnation(event)

    first = strategy.decide(
        knowledge=knowledge,
        position=START,
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )
    assert first is Action.MOVE_FORWARD
    assert strategy.current_target == ALTERNATIVE

    strategy._clear()
    knowledge.mark_safe(Position(2, 2))  # semantic change advances revision
    second = strategy.decide(
        knowledge=knowledge,
        position=START,
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )
    assert second is Action.TURN_RIGHT
    assert strategy.current_target == TARGET


def test_current_position_path_is_not_accepted_as_exploration() -> None:
    knowledge = KnowledgeBase(3, 3)
    knowledge.mark_safe(START)
    strategy = Strategy()

    assert strategy._pursue(knowledge, START, Direction.NORTH, (START,)) is None
    assert strategy.current_target is None


def test_turn_then_move_plan_survives_the_orientation_change() -> None:
    knowledge = KnowledgeBase(3, 3)
    for cell in (START, TARGET):
        knowledge.mark_safe(cell)
    knowledge.mark_visited(START)
    strategy = Strategy()

    first = strategy.decide(
        knowledge=knowledge,
        position=START,
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )
    second = strategy.decide(
        knowledge=knowledge,
        position=START,
        direction=Direction.EAST,
        collected_gold=0,
        glitter=False,
    )

    assert first is Action.TURN_RIGHT
    assert second is Action.MOVE_FORWARD


def test_recovery_can_choose_an_alternative_that_then_makes_progress() -> None:
    knowledge = KnowledgeBase(3, 3)
    for cell in (START, TARGET, ALTERNATIVE):
        knowledge.mark_safe(cell)
    knowledge.mark_visited(START)
    strategy = Strategy()
    strategy.recover_from_stagnation(
        StagnationEvent(START, TARGET, 4, 4, knowledge.revision)
    )

    action = strategy.decide(
        knowledge=knowledge,
        position=START,
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert action is Action.MOVE_FORWARD
    assert strategy.current_target == ALTERNATIVE
