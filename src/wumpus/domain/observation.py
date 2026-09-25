"""Reduced environment-to-agent information surface."""

from dataclasses import dataclass

from wumpus.domain.coordinate import Position
from wumpus.domain.enums import Direction
from wumpus.domain.perception import Perception


@dataclass(frozen=True)
class AgentObservation:
    """The only data the environment may expose to the logical agent."""

    position: Position
    direction: Direction
    perception: Perception
    score: int
    collected_gold: int
    active: bool
