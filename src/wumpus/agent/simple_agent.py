"""Temporary mechanical agent with observable memory and no inference."""

from __future__ import annotations

import random

from wumpus.agent.knowledge import KnowledgeBase
from wumpus.agent.memory import AgentMemory
from wumpus.domain import Action, ActionResult, AgentObservation
from wumpus.game.config import GameConfig, START_DIRECTION, START_POSITION


_MOVEMENT_ACTIONS = (Action.MOVE_FORWARD, Action.TURN_LEFT, Action.TURN_RIGHT)
_MOVEMENT_WEIGHTS = (3, 1, 1)
_TURN_ACTIONS = (Action.TURN_LEFT, Action.TURN_RIGHT)


class SimpleAgent:
    """Decide from observations only, without inference or map knowledge.

    This placeholder keeps an episodic memory so FASE 8 can exercise memory in
    the real loop. Knowledge representation and reasoning begin in FASE 9.
    """

    def __init__(
        self,
        rng: random.Random,
        config: GameConfig | None = None,
    ) -> None:
        game_config = config if config is not None else GameConfig()
        self._rng = rng
        self._blocked = False
        self._memory = AgentMemory(
            START_POSITION,
            START_DIRECTION,
            KnowledgeBase(game_config.rows, game_config.cols),
        )

    @property
    def memory(self) -> AgentMemory:
        return self._memory

    @property
    def actions_taken(self) -> int:
        return len(self._memory.actions)

    def decide(self, observation: AgentObservation) -> Action:
        """Return the next action using only the received observation."""

        self._memory.record_observation(observation)
        if observation.perception.glitter:
            return Action.GRAB
        if observation.collected_gold > 0 and observation.position == START_POSITION:
            return Action.CLIMB
        if self._blocked:
            return self._rng.choice(_TURN_ACTIONS)
        return self._rng.choices(_MOVEMENT_ACTIONS, weights=_MOVEMENT_WEIGHTS)[0]

    def process_result(self, result: ActionResult) -> None:
        """Update the minimal internal state derived from the last result."""

        self._memory.record_result(result)
        self._blocked = result.perception.bump
