"""Enumerations forming the public vocabulary of the game domain."""

from enum import Enum, auto


class Direction(Enum):
    NORTH = auto()
    EAST = auto()
    SOUTH = auto()
    WEST = auto()


class Action(Enum):
    MOVE_FORWARD = auto()
    TURN_RIGHT = auto()
    GRAB = auto()
    SHOOT = auto()
    CLIMB = auto()


class EntityType(Enum):
    EMPTY = auto()
    WUMPUS = auto()
    PIT = auto()
    GOLD = auto()
    BAT = auto()
