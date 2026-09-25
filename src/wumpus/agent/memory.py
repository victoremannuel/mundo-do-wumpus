"""Episodic memory built only from information exposed to the agent."""

from __future__ import annotations

from dataclasses import dataclass

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


class AgentMemory:
    """Remember observable game history without deriving new knowledge."""

    def __init__(
        self,
        initial_position: Position,
        initial_direction: Direction,
    ) -> None:
        self._position = initial_position
        self._direction = initial_direction
        self._visited: set[Position] = {initial_position}
        self._perception_history: list[PerceptionRecord] = []
        self._gold_seen: set[Position] = set()
        self._path: list[Position] = [initial_position]
        self._actions: list[Action] = []
        self._score = 0
        self._collected_gold = 0

    @property
    def position(self) -> Position:
        return self._position

    @property
    def direction(self) -> Direction:
        return self._direction

    @property
    def visited(self) -> frozenset[Position]:
        return frozenset(self._visited)

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

    def record_observation(self, observation: AgentObservation) -> None:
        """Remember the current observable state before a decision."""

        self._remember_position(observation.position)
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
        self._visited.add(position)
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
