"""Domain data transferred after an environment action."""

from dataclasses import dataclass

from wumpus.domain.coordinate import Position
from wumpus.domain.enums import Action, Direction
from wumpus.domain.perception import Perception


@dataclass
class ActionResult:
    action: Action
    position: Position
    direction: Direction
    score_delta: int
    total_score: int
    perception: Perception
    gold_collected: bool = False
    wumpus_killed: bool = False
    teleported: bool = False
    died: bool = False
    escaped: bool = False
