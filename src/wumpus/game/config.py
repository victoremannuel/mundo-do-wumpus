"""Central configuration for a Wumpus World game."""

from dataclasses import dataclass

from wumpus.domain import Direction, Position


START_POSITION = Position(1, 1)
START_DIRECTION = Direction.NORTH

MAX_TURNS = 2000

# The rooms the rules keep free of entities so the agent always starts alive and
# with one legal first move. This is a game rule, not a generation detail, so it
# lives beside the other rules and is re-exported by the generator that enforces
# it and read by the interface that has to validate a player's configuration.
SAFE_INITIAL_CELLS = frozenset(
    {
        Position(1, 1),
        Position(1, 2),
        Position(2, 1),
    }
)


@dataclass
class GameConfig:
    rows: int = 6
    cols: int = 6
    wumpus_count: int = 2
    pit_count: int = 4
    gold_count: int = 3
    bat_count: int = 2

    @property
    def entity_total(self) -> int:
        """How many entities this configuration asks the generator to place."""

        return (
            self.wumpus_count
            + self.pit_count
            + self.gold_count
            + self.bat_count
        )


def available_entity_cells(rows: int, cols: int) -> int:
    """Rooms a map of this size can hold entities in, safe zone excluded.

    Single source of truth for the capacity both the generator and the pre-game
    configuration screen check, so the limit can never drift between the two.
    """

    protected = sum(
        position.is_inside(rows, cols) for position in SAFE_INITIAL_CELLS
    )
    return rows * cols - protected
