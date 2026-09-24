"""Straight-line arrow traversal rules."""

from wumpus.domain import Direction, Position


def line_of_fire(
    origin: Position,
    direction: Direction,
    *,
    rows: int,
    cols: int,
) -> tuple[Position, ...]:
    """Return in-bounds cells from the agent to the wall, nearest first."""

    if direction is Direction.NORTH:
        return tuple(
            Position(row, origin.col)
            for row in range(origin.row + 1, rows + 1)
        )
    if direction is Direction.EAST:
        return tuple(
            Position(origin.row, col)
            for col in range(origin.col + 1, cols + 1)
        )
    if direction is Direction.SOUTH:
        return tuple(
            Position(row, origin.col)
            for row in range(origin.row - 1, 0, -1)
        )
    return tuple(
        Position(origin.row, col)
        for col in range(origin.col - 1, 0, -1)
    )
