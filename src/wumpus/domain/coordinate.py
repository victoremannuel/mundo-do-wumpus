"""Academic, one-based coordinates used by the domain."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Position:
    """A one-based row and column in a rectangular world."""

    row: int
    col: int

    def neighbors(self) -> tuple[Position, Position, Position, Position]:
        """Return the four orthogonally adjacent positions."""

        return (
            Position(self.row + 1, self.col),
            Position(self.row, self.col + 1),
            Position(self.row - 1, self.col),
            Position(self.row, self.col - 1),
        )

    def is_inside(self, rows: int, cols: int) -> bool:
        """Return whether the position is inside one-based world bounds."""

        return 1 <= self.row <= rows and 1 <= self.col <= cols

    def manhattan_distance(self, other: Position) -> int:
        """Return the orthogonal distance to another position."""

        return abs(self.row - other.row) + abs(self.col - other.col)
