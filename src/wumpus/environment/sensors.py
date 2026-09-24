"""Perception derivation from private environment state."""

from collections.abc import Set

from wumpus.domain import Perception, Position


def sense(
    position: Position,
    *,
    alive_wumpus: Set[Position],
    pits: Set[Position],
    bats: Set[Position],
    gold: Set[Position],
    bump: bool,
    scream: bool,
) -> Perception:
    """Build the only perceptual data exposed by the environment."""

    neighbors = set(position.neighbors())
    return Perception(
        stench=bool(neighbors.intersection(alive_wumpus)),
        breeze=bool(neighbors.intersection(pits)),
        bat_noise=bool(neighbors.intersection(bats)),
        glitter=position in gold,
        bump=bump,
        scream=scream,
    )
