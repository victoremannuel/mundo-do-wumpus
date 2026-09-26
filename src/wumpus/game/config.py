"""Central configuration for a Wumpus World game."""

from dataclasses import dataclass
import secrets

from wumpus.domain import Direction, Position


START_POSITION = Position(1, 1)
START_DIRECTION = Direction.NORTH

MAX_TURNS = 2000


def resolve_effective_seed(seed: int | None) -> int:
    """Return the concrete seed that identifies one match.

    Gameplay always receives a dedicated ``random.Random(effective_seed)``.
    ``secrets`` is used only once at the composition boundary when the player
    did not choose a seed; it is never a gameplay random source.
    """

    if seed is None:
        return secrets.randbits(63)
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise TypeError("seed must be an integer or None")
    return seed


def seed_for_restart(base_seed: int, restart_index: int) -> int:
    """Derive a stable, distinct RNG seed for one session in a sequence."""

    if restart_index < 0:
        raise ValueError("restart_index must be non-negative")
    return base_seed + restart_index

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
    def exit_position(self) -> Position:
        """The public structural exit, co-located with the start room."""

        return exit_position_for(self.rows, self.cols)

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
    """Rooms a map of this size can hold entities in, protected cells excluded.

    Single source of truth for the capacity both the generator and the pre-game
    configuration screen check, so the limit can never drift between the two.
    """

    return rows * cols - len(protected_cells(rows, cols))


def exit_position_for(rows: int, cols: int) -> Position:
    """Return the single structural exit for any valid map dimensions.

    The rules deliberately make the spawn room the exit.  Keeping this as a
    function preserves the single public derivation used by the world,
    strategy, and presentation layers.
    """

    del rows, cols
    return START_POSITION


def protected_cells(rows: int, cols: int) -> frozenset[Position]:
    """Return all in-bounds rooms that map generation must keep empty."""

    return frozenset(
        position
        for position in SAFE_INITIAL_CELLS
        if position.is_inside(rows, cols)
    )
