from wumpus.agent import KnowledgeBase, Strategy
from wumpus.domain import Action, Direction, EntityType, Position
from wumpus.game.config import START_POSITION


def safe_knowledge(rows: int, cols: int, safe_cells: list[Position]) -> KnowledgeBase:
    knowledge = KnowledgeBase(rows, cols)
    for cell in safe_cells:
        knowledge.mark_visited(cell)
        knowledge.mark_safe(cell)
    return knowledge


def test_strategy_grabs_gold_regardless_of_the_safe_frontier() -> None:
    knowledge = safe_knowledge(3, 3, [Position(1, 1), Position(1, 2)])
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=True,
    )

    assert action is Action.GRAB


def test_strategy_climbs_at_the_start_with_gold_and_no_safe_frontier() -> None:
    knowledge = safe_knowledge(3, 3, [START_POSITION])
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=START_POSITION,
        direction=Direction.NORTH,
        collected_gold=1,
        glitter=False,
    )

    assert action is Action.CLIMB


def test_strategy_heads_toward_the_start_with_gold_and_no_safe_frontier() -> None:
    knowledge = safe_knowledge(3, 3, [START_POSITION, Position(2, 1), Position(3, 1)])
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(3, 1),
        direction=Direction.NORTH,
        collected_gold=1,
        glitter=False,
    )

    assert action is not Action.CLIMB
    assert action is not None


def test_strategy_explores_the_nearest_unvisited_safe_cell() -> None:
    knowledge = KnowledgeBase(3, 3)
    knowledge.mark_visited(Position(1, 1))
    knowledge.mark_safe(Position(1, 1))
    knowledge.mark_safe(Position(1, 2))
    knowledge.mark_safe(Position(2, 1))
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert action == Action.TURN_RIGHT


def test_strategy_returns_none_when_no_priority_here_applies() -> None:
    knowledge = safe_knowledge(3, 3, [Position(1, 1)])
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert action is None


def test_strategy_reuses_the_queued_plan_across_calls() -> None:
    knowledge = KnowledgeBase(4, 4)
    knowledge.mark_visited(Position(1, 1))
    knowledge.mark_safe(Position(1, 1))
    knowledge.mark_safe(Position(2, 1))
    knowledge.mark_safe(Position(3, 1))
    strategy = Strategy()

    first = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )
    # The caller (AgentMemory, in real use) marks a cell visited once the
    # agent actually arrives there; the test mirrors that before continuing.
    knowledge.mark_visited(Position(2, 1))
    second = strategy.decide(
        knowledge=knowledge,
        position=Position(2, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert first is Action.MOVE_FORWARD
    assert second is Action.MOVE_FORWARD
    assert strategy._target == Position(3, 1)


def test_strategy_replans_after_an_unexpected_teleport() -> None:
    knowledge = KnowledgeBase(4, 4)
    knowledge.mark_visited(Position(1, 1))
    knowledge.mark_safe(Position(1, 1))
    knowledge.mark_safe(Position(2, 1))
    knowledge.mark_safe(Position(3, 1))
    knowledge.mark_visited(Position(1, 3))
    knowledge.mark_safe(Position(1, 3))
    knowledge.mark_safe(Position(1, 2))
    strategy = Strategy()

    strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )
    after_teleport = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 3),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert after_teleport is not None
    assert strategy._path[0] == Position(1, 3)


def test_strategy_replans_after_an_unexpected_bump() -> None:
    knowledge = KnowledgeBase(4, 4)
    knowledge.mark_visited(Position(1, 1))
    knowledge.mark_safe(Position(1, 1))
    knowledge.mark_safe(Position(2, 1))
    strategy = Strategy()

    first = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )
    assert first is Action.MOVE_FORWARD

    repeated = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert repeated is Action.MOVE_FORWARD


def test_strategy_target_selection_is_deterministic() -> None:
    knowledge = KnowledgeBase(3, 3)
    knowledge.mark_visited(Position(1, 1))
    knowledge.mark_safe(Position(1, 1))
    knowledge.mark_safe(Position(1, 2))
    knowledge.mark_safe(Position(2, 1))

    first = Strategy().decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )
    second = Strategy().decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert first == second


def test_strategy_skips_an_unreachable_target_for_a_reachable_one() -> None:
    # Two safe regions separated by an unclassified gap (e.g. after a bat
    # teleport): the nearer candidate by raw distance is not connected
    # through safe cells, so the strategy must fall back to the farther,
    # actually reachable one instead of giving up.
    knowledge = KnowledgeBase(10, 1)
    knowledge.mark_visited(Position(7, 1))
    knowledge.mark_safe(Position(7, 1))
    knowledge.mark_visited(Position(8, 1))
    knowledge.mark_safe(Position(8, 1))
    knowledge.mark_safe(Position(9, 1))  # reachable, distance 2
    knowledge.mark_safe(Position(5, 1))  # unreachable, distance 2, nearer by tie-break
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(7, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert action is not None
    assert strategy._target == Position(9, 1)


def test_strategy_ignores_unsafe_cells_when_no_frontier_is_reachable() -> None:
    knowledge = safe_knowledge(3, 3, [Position(1, 1)])
    knowledge.mark_possible(Position(1, 2), EntityType.PIT)
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert action is None
