"""Temporary policy agent with observable memory and logical inference."""

from __future__ import annotations

import random

from wumpus.agent.inference import InferenceEngine
from wumpus.agent.knowledge import KnowledgeBase
from wumpus.agent.memory import AgentMemory
from wumpus.domain import Action, ActionResult, AgentObservation
from wumpus.game.config import GameConfig, START_DIRECTION, START_POSITION


_MOVEMENT_ACTIONS = (Action.MOVE_FORWARD, Action.TURN_LEFT, Action.TURN_RIGHT)
_MOVEMENT_WEIGHTS = (3, 1, 1)
_TURN_ACTIONS = (Action.TURN_LEFT, Action.TURN_RIGHT)


class SimpleAgent:
    """Update agent-owned knowledge, then choose a temporary mechanical action.

    Inference uses reduced observations only. Planning and strategy remain
    intentionally deferred to their later phases.
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
        self._inference = InferenceEngine(self._memory.knowledge)

    @property
    def memory(self) -> AgentMemory:
        return self._memory

    @property
    def inference(self) -> InferenceEngine:
        return self._inference

    @property
    def actions_taken(self) -> int:
        return len(self._memory.actions)

    def decide(self, observation: AgentObservation) -> Action:
        """Return the next action using only the received observation."""

        self._memory.record_observation(observation)
        self._inference.observe(observation.position, observation.perception)
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
        if not result.died:
            self._inference.observe(result.position, result.perception)
        self._blocked = result.perception.bump
