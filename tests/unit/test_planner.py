from collections import deque

from wumpus.agent import KnowledgeBase, find_path, plan_actions
from wumpus.domain import Action, Direction, EntityType, Position


def safe_knowledge(rows: int, cols: int, safe_cells: list[Position]) -> KnowledgeBase:
    knowledge = KnowledgeBase(rows, cols)
    for cell in safe_cells:
        knowledge.mark_visited(cell)
        knowledge.mark_safe(cell)
    return knowledge


def test_find_path_returns_the_shortest_route_through_safe_cells() -> None:
    knowledge = safe_knowledge(
        4,
        4,
        [
            Position(1, 1),
            Position(2, 1),
            Position(3, 1),
            Position(1, 2),
            Position(1, 3),
        ],
    )

    path = find_path(knowledge, Position(1, 1), Position(3, 1))

    assert path == [Position(1, 1), Position(2, 1), Position(3, 1)]


def test_find_path_never_steps_outside_safe_cells() -> None:
    knowledge = safe_knowledge(
        3,
        3,
        [Position(1, 1), Position(2, 1), Position(2, 2)],
    )
    knowledge.mark_possible(Position(1, 2), EntityType.PIT)

    path = find_path(knowledge, Position(1, 1), Position(2, 2))

    assert path == [Position(1, 1), Position(2, 1), Position(2, 2)]
    assert Position(1, 2) not in path


def test_find_path_returns_none_when_the_goal_is_isolated() -> None:
    knowledge = safe_knowledge(
        3,
        3,
        [Position(1, 1), Position(3, 3)],
    )

    assert find_path(knowledge, Position(1, 1), Position(3, 3)) is None


def test_find_path_returns_none_when_the_goal_is_not_known_safe() -> None:
    knowledge = safe_knowledge(3, 3, [Position(1, 1), Position(2, 1)])

    assert find_path(knowledge, Position(1, 1), Position(3, 3)) is None


def test_find_path_from_a_cell_to_itself_is_trivial() -> None:
    knowledge = safe_knowledge(3, 3, [Position(1, 1)])

    assert find_path(knowledge, Position(1, 1), Position(1, 1)) == [Position(1, 1)]


def test_plan_actions_matches_the_specification_example() -> None:
    path = [Position(2, 1), Position(2, 2)]

    actions = plan_actions(path, Direction.NORTH)

    assert actions == deque([Action.TURN_RIGHT, Action.MOVE_FORWARD])


def test_plan_actions_moves_forward_without_turning_when_already_aligned() -> None:
    path = [Position(1, 1), Position(2, 1)]

    actions = plan_actions(path, Direction.NORTH)

    assert actions == deque([Action.MOVE_FORWARD])


def test_plan_actions_turns_twice_for_a_reversal() -> None:
    path = [Position(2, 1), Position(1, 1)]

    actions = plan_actions(path, Direction.NORTH)

    assert actions == deque(
        [Action.TURN_RIGHT, Action.TURN_RIGHT, Action.MOVE_FORWARD]
    )


def test_plan_actions_accumulates_orientation_across_multiple_steps() -> None:
    path = [Position(1, 1), Position(1, 2), Position(2, 2)]

    actions = plan_actions(path, Direction.NORTH)

    assert actions == deque(
        [
            Action.TURN_RIGHT,
            Action.MOVE_FORWARD,
            Action.TURN_LEFT,
            Action.MOVE_FORWARD,
        ]
    )


def test_plan_actions_for_an_empty_route_is_empty() -> None:
    assert plan_actions([Position(1, 1)], Direction.NORTH) == deque()
