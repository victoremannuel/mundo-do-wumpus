"""Logical map owned by the agent and isolated from the real environment."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from wumpus.domain import EntityType, Position


HAZARD_TYPES = (EntityType.PIT, EntityType.WUMPUS, EntityType.BAT)


class KnowledgeConflictError(ValueError):
    """Raised when a classification contradicts established knowledge."""


@dataclass(frozen=True)
class KnownCell:
    """Immutable logical classification for one cell."""

    visited: bool
    safe: bool
    possible_pit: bool
    possible_wumpus: bool
    possible_bat: bool
    confirmed_pit: bool
    confirmed_wumpus: bool
    confirmed_bat: bool
    dead_wumpus: bool
    not_pit: bool
    not_wumpus: bool
    not_bat: bool


class KnowledgeBase:
    """Store explicit logical classifications without running inference rules."""

    def __init__(self, rows: int, cols: int) -> None:
        if rows < 1 or cols < 1:
            raise ValueError("Knowledge map dimensions must be positive")

        self._rows = rows
        self._cols = cols
        self._all_cells = frozenset(
            Position(row, col)
            for row in range(1, rows + 1)
            for col in range(1, cols + 1)
        )
        self._visited: set[Position] = set()
        self._safe: set[Position] = set()
        self._possible = {hazard: set() for hazard in HAZARD_TYPES}
        self._confirmed = {hazard: set() for hazard in HAZARD_TYPES}
        self._dead_wumpus: set[Position] = set()
        self._negative = {hazard: set() for hazard in HAZARD_TYPES}
        self._revision = 0

    @property
    def rows(self) -> int:
        return self._rows

    @property
    def cols(self) -> int:
        return self._cols

    @property
    def revision(self) -> int:
        return self._revision

    @property
    def all_cells(self) -> frozenset[Position]:
        return self._all_cells

    @property
    def visited(self) -> frozenset[Position]:
        return frozenset(self._visited)

    @property
    def safe(self) -> frozenset[Position]:
        return frozenset(self._safe)

    @property
    def unknown(self) -> frozenset[Position]:
        classified = self._safe.union(
            *self._possible.values(),
            *self._confirmed.values(),
        )
        return self._all_cells.difference(classified)

    @property
    def frontier(self) -> frozenset[Position]:
        return frozenset(
            neighbor
            for position in self._visited
            for neighbor in position.neighbors()
            if neighbor in self._all_cells and neighbor not in self._visited
        )

    @property
    def possible_pits(self) -> frozenset[Position]:
        return self._positions(self._possible, EntityType.PIT)

    @property
    def possible_wumpus(self) -> frozenset[Position]:
        return self._positions(self._possible, EntityType.WUMPUS)

    @property
    def possible_bats(self) -> frozenset[Position]:
        return self._positions(self._possible, EntityType.BAT)

    @property
    def confirmed_pits(self) -> frozenset[Position]:
        return self._positions(self._confirmed, EntityType.PIT)

    @property
    def confirmed_wumpus(self) -> frozenset[Position]:
        return self._positions(self._confirmed, EntityType.WUMPUS)

    @property
    def confirmed_bats(self) -> frozenset[Position]:
        return self._positions(self._confirmed, EntityType.BAT)

    @property
    def dead_wumpus(self) -> frozenset[Position]:
        return frozenset(self._dead_wumpus)

    @property
    def not_pit(self) -> frozenset[Position]:
        return self._positions(self._negative, EntityType.PIT)

    @property
    def not_wumpus(self) -> frozenset[Position]:
        return self._positions(self._negative, EntityType.WUMPUS)

    @property
    def not_bat(self) -> frozenset[Position]:
        return self._positions(self._negative, EntityType.BAT)

    def cell(self, position: Position) -> KnownCell:
        """Return an immutable logical-map snapshot for one position."""

        self._require_position(position)
        return KnownCell(
            visited=position in self._visited,
            safe=position in self._safe,
            possible_pit=position in self._possible[EntityType.PIT],
            possible_wumpus=position in self._possible[EntityType.WUMPUS],
            possible_bat=position in self._possible[EntityType.BAT],
            confirmed_pit=position in self._confirmed[EntityType.PIT],
            confirmed_wumpus=position in self._confirmed[EntityType.WUMPUS],
            confirmed_bat=position in self._confirmed[EntityType.BAT],
            dead_wumpus=position in self._dead_wumpus,
            not_pit=position in self._negative[EntityType.PIT],
            not_wumpus=position in self._negative[EntityType.WUMPUS],
            not_bat=position in self._negative[EntityType.BAT],
        )

    def mark_visited(self, position: Position) -> bool:
        """Record that the agent physically reached a cell."""

        self._require_position(position)
        return self._apply(lambda: self._visited.add(position))

    def mark_safe(self, position: Position) -> bool:
        """Classify a cell as free of every hazard type."""

        self._require_position(position)
        if any(position in positions for positions in self._confirmed.values()):
            raise KnowledgeConflictError("A confirmed hazard cannot be marked safe")

        def update() -> None:
            self._safe.add(position)
            for hazard in HAZARD_TYPES:
                self._possible[hazard].discard(position)
                self._negative[hazard].add(position)

        return self._apply(update)

    def mark_possible(self, position: Position, hazard: EntityType) -> bool:
        """Record a hazard hypothesis without confirming it."""

        self._require_position(position)
        self._require_hazard(hazard)
        if position in self._safe or position in self._negative[hazard]:
            raise KnowledgeConflictError("A ruled-out hazard cannot be possible")
        if any(
            position in positions
            for known_hazard, positions in self._confirmed.items()
            if known_hazard is not hazard
        ):
            raise KnowledgeConflictError("A cell cannot contain two hazard types")
        if position in self._confirmed[hazard]:
            return False
        return self._apply(lambda: self._possible[hazard].add(position))

    def mark_confirmed(self, position: Position, hazard: EntityType) -> bool:
        """Promote a compatible hazard hypothesis to confirmed knowledge."""

        self._require_position(position)
        self._require_hazard(hazard)
        if position in self._safe or position in self._negative[hazard]:
            raise KnowledgeConflictError("A ruled-out hazard cannot be confirmed")
        if any(
            position in positions
            for known_hazard, positions in self._confirmed.items()
            if known_hazard is not hazard
        ):
            raise KnowledgeConflictError("A cell cannot contain two hazard types")

        def update() -> None:
            self._confirmed[hazard].add(position)
            for candidate in HAZARD_TYPES:
                self._possible[candidate].discard(position)
                if candidate is not hazard:
                    self._negative[candidate].add(position)

        return self._apply(update)

    def mark_not(self, position: Position, hazard: EntityType) -> bool:
        """Record explicit negative knowledge for one hazard type."""

        self._require_position(position)
        self._require_hazard(hazard)
        if position in self._confirmed[hazard]:
            raise KnowledgeConflictError("A confirmed hazard cannot be ruled out")

        def update() -> None:
            self._negative[hazard].add(position)
            self._possible[hazard].discard(position)
            if all(position in self._negative[item] for item in HAZARD_TYPES):
                self._safe.add(position)

        return self._apply(update)

    def mark_wumpus_dead(self, position: Position) -> bool:
        """Transition a confirmed live Wumpus to dead, non-hazard knowledge."""

        self._require_position(position)
        if position in self._dead_wumpus:
            return False
        if position not in self._confirmed[EntityType.WUMPUS]:
            raise KnowledgeConflictError("Only a confirmed Wumpus can be marked dead")

        def update() -> None:
            self._confirmed[EntityType.WUMPUS].remove(position)
            self._possible[EntityType.WUMPUS].discard(position)
            self._dead_wumpus.add(position)
            self._negative[EntityType.WUMPUS].add(position)
            if all(position in self._negative[item] for item in HAZARD_TYPES):
                self._safe.add(position)

        return self._apply(update)

    def _apply(self, update: Callable[[], None]) -> bool:
        before = self._signature()
        update()
        if self._signature() == before:
            return False
        self._revision += 1
        return True

    def _signature(self) -> tuple[object, ...]:
        return (
            frozenset(self._visited),
            frozenset(self._safe),
            *(frozenset(self._possible[item]) for item in HAZARD_TYPES),
            *(frozenset(self._confirmed[item]) for item in HAZARD_TYPES),
            frozenset(self._dead_wumpus),
            *(frozenset(self._negative[item]) for item in HAZARD_TYPES),
        )

    def _require_position(self, position: Position) -> None:
        if position not in self._all_cells:
            raise ValueError(f"Position outside knowledge map: {position}")

    @staticmethod
    def _require_hazard(hazard: EntityType) -> None:
        if hazard not in HAZARD_TYPES:
            raise ValueError(f"Not a hazard type: {hazard}")

    @staticmethod
    def _positions(
        source: dict[EntityType, set[Position]],
        hazard: EntityType,
    ) -> frozenset[Position]:
        return frozenset(source[hazard])
