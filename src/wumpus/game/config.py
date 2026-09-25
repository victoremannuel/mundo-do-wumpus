"""Central configuration for a Wumpus World game."""

from dataclasses import dataclass

from wumpus.domain import Direction, Position


START_POSITION = Position(1, 1)
START_DIRECTION = Direction.NORTH

MAX_TURNS = 2000


@dataclass
class GameConfig:
    rows: int = 6
    cols: int = 6
    wumpus_count: int = 2
    pit_count: int = 4
    gold_count: int = 3
    bat_count: int = 2
