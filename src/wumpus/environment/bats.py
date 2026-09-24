"""Bounded, injected-RNG selection for bat teleport destinations."""

from __future__ import annotations

import random
from collections.abc import Set

from wumpus.domain import Position


MAX_BAT_TELEPORT_CHAIN = 100
BAT_CHAIN_LIMIT_EVENT = (
    "Bat teleport chain limit reached; selected a non-bat destination."
)


class BatTeleportError(RuntimeError):
    """Raised when a bat chain has no possible non-bat fallback."""


def choose_teleport_destination(
    rng: random.Random,
    *,
    rows: int,
    cols: int,
    excluded: Set[Position] = frozenset(),
) -> Position:
    """Choose one in-bounds destination, optionally excluding positions."""

    candidates = tuple(
        Position(row, col)
        for row in range(1, rows + 1)
        for col in range(1, cols + 1)
        if Position(row, col) not in excluded
    )
    if not candidates:
        raise BatTeleportError("No non-bat teleport destination is available")
    return rng.choice(candidates)
