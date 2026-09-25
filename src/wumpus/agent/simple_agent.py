"""Logical agent combining memory, inference, and the FASE 12 strategy."""

from __future__ import annotations

import random

from wumpus.agent.inference import InferenceEngine
from wumpus.agent.knowledge import KnowledgeBase
from wumpus.agent.memory import AgentMemory
from wumpus.agent.strategy import Strategy
from wumpus.domain import Action, ActionResult, AgentObservation
from wumpus.game.config import GameConfig, START_DIRECTION, START_POSITION


_MOVEMENT_ACTIONS = (Action.MOVE_FORWARD, Action.TURN_LEFT, Action.TURN_RIGHT)
_MOVEMENT_WEIGHTS = (3, 1, 1)
_TURN_ACTIONS = (Action.TURN_LEFT, Action.TURN_RIGHT)


class SimpleAgent:
    """Update agent-owned knowledge, then apply the FASE 12 decision hierarchy.

    Inference and planning use reduced observations only. When the strategy
    finds no known-safe target (priorities 5-7: shooting, risk-based choice,
    and forced return require FASE 13 and FASE 14), a bounded random fallback
    keeps the agent moving without claiming those later priorities.
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
        self._strategy = Strategy()

    @property
    def memory(self) -> AgentMemory:
        return self._memory

    @property
    def inference(self) -> InferenceEngine:
        return self._inference

    @property
    def strategy(self) -> Strategy:
        return self._strategy

    @property
    def actions_taken(self) -> int:
        return len(self._memory.actions)

    def decide(self, observation: AgentObservation) -> Action:
        """Return the next action using only the received observation."""

        self._memory.record_observation(observation)
        self._inference.observe(observation.position, observation.perception)

        action = self._strategy.decide(
            knowledge=self._memory.knowledge,
            position=observation.position,
            direction=observation.direction,
            collected_gold=observation.collected_gold,
            glitter=observation.perception.glitter,
        )
        if action is not None:
            return action

        if self._blocked:
            return self._rng.choice(_TURN_ACTIONS)
        return self._rng.choices(_MOVEMENT_ACTIONS, weights=_MOVEMENT_WEIGHTS)[0]

    def process_result(self, result: ActionResult) -> None:
        """Update the minimal internal state derived from the last result."""

        self._memory.record_result(result)
        if not result.died:
            self._inference.observe(result.position, result.perception)
        self._blocked = result.perception.bump
