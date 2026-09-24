"""Central configuration for a Wumpus World game."""

from dataclasses import dataclass


@dataclass
class GameConfig:
    rows: int = 6
    cols: int = 6
    wumpus_count: int = 2
    pit_count: int = 4
    gold_count: int = 3
    bat_count: int = 2
