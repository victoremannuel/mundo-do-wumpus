"""Deterministic logical inference over the agent-owned knowledge base."""

from __future__ import annotations

from dataclasses import dataclass

from wumpus.agent.knowledge import HAZARD_TYPES, KnowledgeBase
from wumpus.domain import EntityType, Perception, Position


MAX_INFERENCE_CYCLES = 100


class InferenceLimitError(RuntimeError):
    """Raised when inference does not reach a fixed point within its limit."""


class InferenceConflictError(RuntimeError):
    """Raised when observed evidence has no compatible hazard placement."""


@dataclass(frozen=True)
class InferenceEvent:
    """Functional explanation of one knowledge-changing rule application."""

    rule: str
    source: Position | None
    affected: tuple[Position, ...]


class InferenceEngine:
    """Apply sensor rules until the logical knowledge reaches a fixed point."""

    def __init__(
        self,
        knowledge: KnowledgeBase,
        *,
        max_cycles: int = MAX_INFERENCE_CYCLES,
    ) -> None:
        if max_cycles < 1:
            raise ValueError("max_cycles must be at least 1")
        self._knowledge = knowledge
        self._max_cycles = max_cycles
        self._observations: dict[Position, Perception] = {}
        self._events: list[InferenceEvent] = []

    @property
    def events(self) -> tuple[InferenceEvent, ...]:
        return tuple(self._events)

    def observe(self, position: Position, perception: Perception) -> None:
        """Register a perception and infer every consequence to a fixed point."""

        if position not in self._knowledge.all_cells:
            raise ValueError(f"Observation outside knowledge map: {position}")
        self._knowledge.mark_visited(position)
        self._knowledge.mark_safe(position)
        self._observations[position] = perception
        self._infer_to_fixed_point()

    def _infer_to_fixed_point(self) -> None:
        for _ in range(self._max_cycles):
            revision_before = self._knowledge.revision
            self._apply_negative_rules()
            self._update_candidates()
            self._confirm_by_elimination()
            if self._knowledge.revision == revision_before:
                return
        raise InferenceLimitError(
            f"Inference did not stabilize within {self._max_cycles} cycles"
        )

    def _apply_negative_rules(self) -> None:
        for source, perception in self._observations.items():
            for hazard in HAZARD_TYPES:
                if self._signal(perception, hazard):
                    continue
                changed = tuple(
                    position
                    for position in self._neighbors(source)
                    if self._knowledge.mark_not(position, hazard)
                )
                self._record(
                    f"NO_{hazard.name}_SIGNAL",
                    source,
                    changed,
                )

    def _update_candidates(self) -> None:
        for source, perception in self._observations.items():
            for hazard in HAZARD_TYPES:
                if not self._signal(perception, hazard):
                    continue
                candidates = self._constraint_candidates(source, hazard)
                if self._confirmed(hazard).intersection(candidates):
                    continue
                if not candidates:
                    raise InferenceConflictError(
                        f"{hazard.name} signal at {source} has no valid candidate"
                    )
                changed = tuple(
                    position
                    for position in candidates
                    if self._knowledge.mark_possible(position, hazard)
                )
                self._record(
                    f"{hazard.name}_SIGNAL_ADDS_CANDIDATES",
                    source,
                    changed,
                )

    def _confirm_by_elimination(self) -> None:
        for source, perception in self._observations.items():
            for hazard in HAZARD_TYPES:
                if not self._signal(perception, hazard):
                    continue
                candidates = self._constraint_candidates(source, hazard)
                if self._confirmed(hazard).intersection(candidates):
                    continue
                if len(candidates) == 1:
                    position = next(iter(candidates))
                    if self._knowledge.mark_confirmed(position, hazard):
                        self._record(
                            f"{hazard.name}_CONFIRMED_BY_ELIMINATION",
                            source,
                            (position,),
                        )

    def _constraint_candidates(
        self,
        source: Position,
        hazard: EntityType,
    ) -> frozenset[Position]:
        """Return the domain of one positive existential sensor constraint.

        Domains from distinct positive observations are intentionally not
        intersected: valid worlds may contain multiple hazards of each type.
        """

        ruled_out = self._negative(hazard)
        return frozenset(
            position
            for position in self._neighbors(source)
            if position not in ruled_out
            and position not in self._knowledge.safe
            and not self._confirmed_other_hazard(position, hazard)
        )

    def _neighbors(self, source: Position) -> tuple[Position, ...]:
        return tuple(
            position
            for position in source.neighbors()
            if position in self._knowledge.all_cells
        )

    def _confirmed_other_hazard(
        self,
        position: Position,
        hazard: EntityType,
    ) -> bool:
        return any(
            position in self._confirmed(candidate)
            for candidate in HAZARD_TYPES
            if candidate is not hazard
        )

    def _negative(self, hazard: EntityType) -> frozenset[Position]:
        return {
            EntityType.PIT: self._knowledge.not_pit,
            EntityType.WUMPUS: self._knowledge.not_wumpus,
            EntityType.BAT: self._knowledge.not_bat,
        }[hazard]

    def _confirmed(self, hazard: EntityType) -> frozenset[Position]:
        return {
            EntityType.PIT: self._knowledge.confirmed_pits,
            EntityType.WUMPUS: self._knowledge.confirmed_wumpus,
            EntityType.BAT: self._knowledge.confirmed_bats,
        }[hazard]

    @staticmethod
    def _signal(perception: Perception, hazard: EntityType) -> bool:
        return {
            EntityType.PIT: perception.breeze,
            EntityType.WUMPUS: perception.stench,
            EntityType.BAT: perception.bat_noise,
        }[hazard]

    def _record(
        self,
        rule: str,
        source: Position | None,
        affected: tuple[Position, ...],
    ) -> None:
        if affected:
            self._events.append(
                InferenceEvent(
                    rule=rule,
                    source=source,
                    affected=tuple(sorted(affected)),
                )
            )
