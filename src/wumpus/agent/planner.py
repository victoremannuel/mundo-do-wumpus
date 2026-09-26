"""Deterministic BFS route planning over agent-owned safe knowledge."""

from __future__ import annotations

from collections import deque

from wumpus.agent.knowledge import KnowledgeBase
from wumpus.domain import Action, Direction, Position


_RIGHT_TURN = {
    Direction.NORTH: Direction.EAST,
    Direction.EAST: Direction.SOUTH,
    Direction.SOUTH: Direction.WEST,
    Direction.WEST: Direction.NORTH,
}

FORWARD_DELTA = {
    Direction.NORTH: (1, 0),
    Direction.EAST: (0, 1),
    Direction.SOUTH: (-1, 0),
    Direction.WEST: (0, -1),
}

_DELTA_TO_DIRECTION = {delta: direction for direction, delta in FORWARD_DELTA.items()}


def find_path(
    knowledge: KnowledgeBase,
    start: Position,
    goal: Position,
) -> list[Position] | None:
    """Return the shortest route between two safe cells, or ``None``.

    The route is a breadth-first search restricted to cells the agent has
    classified ``safe``. ``start`` is accepted without a safety check because
    it is always the agent's own current position, which callers derive from
    already-verified knowledge.
    """

    if start == goal:
        return [start]
    if goal not in knowledge.safe:
        return None

    frontier: deque[Position] = deque([start])
    came_from: dict[Position, Position] = {}
    visited = {start}

    while frontier:
        current = frontier.popleft()
        for neighbor in current.neighbors():
            if neighbor in visited or neighbor not in knowledge.safe:
                continue
            visited.add(neighbor)
            came_from[neighbor] = current
            if neighbor == goal:
                return _reconstruct(came_from, start, goal)
            frontier.append(neighbor)

    return None


def _reconstruct(
    came_from: dict[Position, Position],
    start: Position,
    goal: Position,
) -> list[Position]:
    path = [goal]
    while path[-1] != start:
        path.append(came_from[path[-1]])
    path.reverse()
    return path


def plan_actions(path: list[Position], direction: Direction) -> deque[Action]:
    """Convert a route of positions into a queue of discrete agent actions."""

    actions: deque[Action] = deque()
    current_direction = direction
    for current, next_position in zip(path, path[1:]):
        delta = (
            next_position.row - current.row,
            next_position.col - current.col,
        )
        required_direction = _DELTA_TO_DIRECTION[delta]
        actions.extend(turns_to_face(current_direction, required_direction))
        actions.append(Action.MOVE_FORWARD)
        current_direction = required_direction
    return actions


def turns_to_face(current: Direction, target: Direction) -> tuple[Action, ...]:
    """Return the 0-3 `TURN_RIGHT` actions that reorient one facing onto another.

    `TURN_LEFT` is not a canonical action: a 90-degree left turn is expressed
    as three real `TURN_RIGHT` actions, each costing its own action point.
    """

    if current == target:
        return ()
    if _RIGHT_TURN[current] == target:
        return (Action.TURN_RIGHT,)
    if _RIGHT_TURN[_RIGHT_TURN[current]] == target:
        return (Action.TURN_RIGHT, Action.TURN_RIGHT)
    return (Action.TURN_RIGHT, Action.TURN_RIGHT, Action.TURN_RIGHT)
