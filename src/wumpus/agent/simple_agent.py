"""Logical agent combining memory, inference, strategy, and exit policy."""

from __future__ import annotations

import random

from wumpus.agent.inference import InferenceEngine
from wumpus.agent.knowledge import KnowledgeBase
from wumpus.agent.memory import AgentMemory
from wumpus.agent.reasoning import DecisionReason
from wumpus.agent.strategy import Strategy
from wumpus.domain import Action, ActionResult, AgentObservation
from wumpus.game.config import GameConfig, START_DIRECTION, START_POSITION


class SimpleAgent:
    """Update agent-owned knowledge, then apply the decision hierarchy.

    Inference, planning, hunting, least-risk exploration, and rational exit
    decisions use reduced observations only. Strategy owns every outcome,
    including a deterministic in-place turn when no safe return path or
    acceptable risk step is known, so no knowledge-blind movement fallback
    can override rational abandonment.
    """

    def __init__(
        self,
        rng: random.Random,
        config: GameConfig | None = None,
    ) -> None:
        game_config = config if config is not None else GameConfig()
        self._memory = AgentMemory(
            START_POSITION,
            START_DIRECTION,
            KnowledgeBase(game_config.rows, game_config.cols),
        )
        self._inference = InferenceEngine(self._memory.knowledge)
        self._strategy = Strategy(total_gold=game_config.gold_count)

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

    @property
    def last_reason(self) -> DecisionReason | None:
        return self._strategy.last_reason

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
        return action

    def process_result(self, result: ActionResult) -> None:
        """Update the minimal internal state derived from the last result."""

        self._memory.record_result(result)
        if result.action is Action.SHOOT:
            # Reconcile the kill before inference sees the post-shot
            # perception: a freshly dead Wumpus stops emitting stench, and
            # inference must not find the now-safe cell still "confirmed".
            self._strategy.confirm_kill(self._memory.knowledge, result)
        if not result.died:
            self._inference.observe(result.position, result.perception)
