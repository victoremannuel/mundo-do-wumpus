"""Episodic memory built only from information exposed to the agent."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from wumpus.agent.knowledge import KnowledgeBase
from wumpus.domain import (
    Action,
    ActionResult,
    AgentObservation,
    Direction,
    Perception,
    Position,
)


@dataclass(frozen=True)
class PerceptionRecord:
    """One perception received before or immediately after an action."""

    position: Position
    direction: Direction
    perception: Perception
    score: int
    action: Action | None = None


MAX_TURNS_WITHOUT_PROGRESS = 6
MAX_CONSECUTIVE_ROTATIONS = 4


@dataclass(frozen=True)
class StagnationEvent:
    """Observable evidence that execution stopped making semantic progress."""

    position: Position
    objective: Position | None
    rotations: int
    turns_without_progress: int
    knowledge_revision: int


@dataclass(frozen=True)
class _PendingAction:
    position: Position
    knowledge_revision: int
    objective: Position | None


class AgentMemory:
    """Remember observable game history without deriving new knowledge."""

    def __init__(
        self,
        initial_position: Position,
        initial_direction: Direction,
        knowledge: KnowledgeBase,
    ) -> None:
        knowledge.mark_visited(initial_position)
        knowledge.mark_safe(initial_position)
        self._position = initial_position
        self._direction = initial_direction
        self._knowledge = knowledge
        self._perception_history: list[PerceptionRecord] = []
        self._gold_seen: set[Position] = set()
        self._path: list[Position] = [initial_position]
        self._actions: list[Action] = []
        self._score = 0
        self._collected_gold = 0
        self._pending_action: _PendingAction | None = None
        self._recent_positions: deque[Position] = deque(maxlen=8)
        self._recent_actions: deque[Action] = deque(maxlen=8)
        self._recent_objectives: deque[Position | None] = deque(maxlen=8)
        self._recent_state_signatures: deque[tuple[Position, Position | None, int]] = (
            deque(maxlen=8)
        )
        self._turns_without_progress = 0
        self._consecutive_rotations = 0

    @property
    def position(self) -> Position:
        return self._position

    @property
    def direction(self) -> Direction:
        return self._direction

    @property
    def visited(self) -> frozenset[Position]:
        return self._knowledge.visited

    @property
    def knowledge(self) -> KnowledgeBase:
        return self._knowledge

    @property
    def perception_history(self) -> tuple[PerceptionRecord, ...]:
        return tuple(self._perception_history)

    @property
    def gold_seen(self) -> frozenset[Position]:
        return frozenset(self._gold_seen)

    @property
    def path(self) -> tuple[Position, ...]:
        return tuple(self._path)

    @property
    def actions(self) -> tuple[Action, ...]:
        return tuple(self._actions)

    @property
    def score(self) -> int:
        return self._score

    @property
    def collected_gold(self) -> int:
        return self._collected_gold

    @property
    def turns_without_progress(self) -> int:
        return self._turns_without_progress

    @property
    def recent_actions(self) -> tuple[Action, ...]:
        return tuple(self._recent_actions)

    @property
    def recent_state_signatures(self) -> tuple[tuple[Position, Position | None, int], ...]:
        return tuple(self._recent_state_signatures)

    def begin_action(self, objective: Position | None) -> None:
        """Snapshot observable state after deciding, before execution."""

        self._pending_action = _PendingAction(
            position=self._position,
            knowledge_revision=self._knowledge.revision,
            objective=objective,
        )

    def finish_action(self, result: ActionResult) -> StagnationEvent | None:
        """Classify the completed action without retaining hidden world state."""

        pending = self._pending_action
        self._pending_action = None
        if pending is None:
            return None

        revision = self._knowledge.revision
        progress = (
            result.position != pending.position
            or revision != pending.knowledge_revision
            or result.gold_collected
            or result.wumpus_killed
            or result.teleported
            or result.died
            or result.escaped
        )
        self._recent_positions.append(result.position)
        self._recent_actions.append(result.action)
        self._recent_objectives.append(pending.objective)
        self._recent_state_signatures.append(
            (result.position, pending.objective, revision)
        )
        if progress:
            self._turns_without_progress = 0
            self._consecutive_rotations = 0
            return None

        self._turns_without_progress += 1
        if result.action in (Action.TURN_LEFT, Action.TURN_RIGHT):
            self._consecutive_rotations += 1
        else:
            self._consecutive_rotations = 0

        if (
            self._consecutive_rotations >= MAX_CONSECUTIVE_ROTATIONS
            or self._turns_without_progress >= MAX_TURNS_WITHOUT_PROGRESS
        ):
            event = StagnationEvent(
                position=result.position,
                objective=pending.objective,
                rotations=self._consecutive_rotations,
                turns_without_progress=self._turns_without_progress,
                knowledge_revision=revision,
            )
            self._turns_without_progress = 0
            self._consecutive_rotations = 0
            return event
        return None

    def record_observation(self, observation: AgentObservation) -> None:
        """Remember the current observable state before a decision."""

        self._remember_position(observation.position)
        if observation.active:
            self._knowledge.mark_safe(observation.position)
        self._direction = observation.direction
        self._score = observation.score
        self._collected_gold = observation.collected_gold
        self._remember_perception(
            position=observation.position,
            direction=observation.direction,
            perception=observation.perception,
            score=observation.score,
        )

    def record_result(self, result: ActionResult) -> None:
        """Remember an executed action and its directly observable result."""

        self._actions.append(result.action)
        self._remember_position(result.position)
        if not result.died:
            self._knowledge.mark_safe(result.position)
        self._direction = result.direction
        self._score = result.total_score
        if result.gold_collected:
            self._collected_gold += 1
        self._remember_perception(
            position=result.position,
            direction=result.direction,
            perception=result.perception,
            score=result.total_score,
            action=result.action,
        )

    def _remember_position(self, position: Position) -> None:
        self._position = position
        self._knowledge.mark_visited(position)
        if position != self._path[-1]:
            self._path.append(position)

    def _remember_perception(
        self,
        *,
        position: Position,
        direction: Direction,
        perception: Perception,
        score: int,
        action: Action | None = None,
    ) -> None:
        if perception.glitter:
            self._gold_seen.add(position)
        self._perception_history.append(
            PerceptionRecord(
                position=position,
                direction=direction,
                perception=perception,
                score=score,
                action=action,
            )
        )
