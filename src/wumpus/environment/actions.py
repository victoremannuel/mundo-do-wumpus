"""Deterministic movement and rotation rules."""

from wumpus.domain import Action, Direction, Position


_RIGHT_TURN = {
    Direction.NORTH: Direction.EAST,
    Direction.EAST: Direction.SOUTH,
    Direction.SOUTH: Direction.WEST,
    Direction.WEST: Direction.NORTH,
}

_FORWARD_DELTA = {
    Direction.NORTH: (1, 0),
    Direction.EAST: (0, 1),
    Direction.SOUTH: (-1, 0),
    Direction.WEST: (0, -1),
}


def rotated(direction: Direction, action: Action) -> Direction:
    """Return the direction produced by a right turn."""

    if action is Action.TURN_RIGHT:
        return _RIGHT_TURN[direction]
    raise ValueError(f"Action does not rotate the agent: {action}")


def forward_position(position: Position, direction: Direction) -> Position:
    """Return the position one step ahead without applying wall bounds."""

    row_delta, col_delta = _FORWARD_DELTA[direction]
    return Position(position.row + row_delta, position.col + col_delta)
