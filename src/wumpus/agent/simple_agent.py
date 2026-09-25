"""Temporary mechanical agent used to exercise the loop in FASE 7."""

from __future__ import annotations

import random

from wumpus.domain import Action, ActionResult, AgentObservation
from wumpus.game.config import START_POSITION


_MOVEMENT_ACTIONS = (Action.MOVE_FORWARD, Action.TURN_LEFT, Action.TURN_RIGHT)
_MOVEMENT_WEIGHTS = (3, 1, 1)
_TURN_ACTIONS = (Action.TURN_LEFT, Action.TURN_RIGHT)


class SimpleAgent:
    """Decide from observations only, without any reasoning or memory of the map.

    This placeholder proves the game loop works mechanically. The reasoning
    agent replaces it from FASE 8 onwards.
    """

    def __init__(self, rng: random.Random) -> None:
        self._rng = rng
        self._blocked = False
        self._actions_taken = 0

    @property
    def actions_taken(self) -> int:
        return self._actions_taken

    def decide(self, observation: AgentObservation) -> Action:
        """Return the next action using only the received observation."""

        if observation.perception.glitter:
            return Action.GRAB
        if observation.collected_gold > 0 and observation.position == START_POSITION:
            return Action.CLIMB
        if self._blocked:
            return self._rng.choice(_TURN_ACTIONS)
        return self._rng.choices(_MOVEMENT_ACTIONS, weights=_MOVEMENT_WEIGHTS)[0]

    def process_result(self, result: ActionResult) -> None:
        """Update the minimal internal state derived from the last result."""

        self._actions_taken += 1
        self._blocked = result.perception.bump
