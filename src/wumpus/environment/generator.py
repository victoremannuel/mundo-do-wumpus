"""Procedural generation of hidden Wumpus World maps."""

from __future__ import annotations

import random
from collections import Counter, deque
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from wumpus.domain import EntityType, Position
from wumpus.game.config import (
    SAFE_INITIAL_CELLS,
    START_POSITION,
    GameConfig,
    available_entity_cells,
    protected_cells,
)
from wumpus.game.objective import GameObjective


__all__ = (
    "SAFE_INITIAL_CELLS",
    "GeneratedMap",
    "MapGenerationError",
    "MapGenerator",
    "is_winnable",
)


MAX_GENERATION_ATTEMPTS = 256
_BLOCKING_ENTITIES = frozenset({EntityType.PIT, EntityType.WUMPUS, EntityType.BAT})


class MapGenerationError(ValueError):
    """Raised when a configuration cannot produce a valid map."""


@dataclass(frozen=True)
class GeneratedMap:
    """A generated map that remains private to the environment layer."""

    rows: int
    cols: int
    entities: Mapping[Position, EntityType]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "entities",
            MappingProxyType(dict(self.entities)),
        )

    def entity_at(self, position: Position) -> EntityType:
        """Return the entity at an in-bounds position."""

        if not position.is_inside(self.rows, self.cols):
            raise ValueError(f"Position outside generated map: {position}")
        return self.entities.get(position, EntityType.EMPTY)


def is_winnable(
    generated_map: GeneratedMap,
    objective: GameObjective,
    config: GameConfig,
) -> bool:
    """Return whether the selected objective has a hazard-free physical route."""

    start = START_POSITION
    exit_position = config.exit_position
    if not start.is_inside(generated_map.rows, generated_map.cols):
        return False
    reachable = {start}
    pending = deque([start])
    while pending:
        position = pending.popleft()
        for candidate in (
            Position(position.row - 1, position.col),
            Position(position.row + 1, position.col),
            Position(position.row, position.col - 1),
            Position(position.row, position.col + 1),
        ):
            if (
                not candidate.is_inside(generated_map.rows, generated_map.cols)
                or candidate in reachable
                or generated_map.entity_at(candidate) in _BLOCKING_ENTITIES
            ):
                continue
            reachable.add(candidate)
            pending.append(candidate)
    if exit_position not in reachable:
        return False
    if objective is GameObjective.ESCAPE_FAST:
        return True
    if objective is GameObjective.COLLECT_ALL_GOLD:
        return all(
            position in reachable
            for position, entity in generated_map.entities.items()
            if entity is EntityType.GOLD
        )
    raise AssertionError(f"Unsupported game objective: {objective!r}")


class MapGenerator:
    """Generate maps using only the injected pseudo-random generator."""

    def __init__(
        self,
        rng: random.Random,
        config: GameConfig | None = None,
        *,
        objective: GameObjective = GameObjective.COLLECT_ALL_GOLD,
    ) -> None:
        self._rng = rng
        self._config = config if config is not None else GameConfig()
        self._objective = objective

    def generate(self) -> GeneratedMap:
        """Generate one map and validate every structural invariant."""

        available = self._available_positions()
        self._validate_winnability_capacity()
        for _ in range(MAX_GENERATION_ATTEMPTS):
            generated_map = self._candidate(available)
            if is_winnable(generated_map, self._objective, self._config):
                self._validate(generated_map)
                return generated_map
        generated_map = self._construct_winnable_map(available)
        self._validate(generated_map)
        return generated_map

    def _candidate(self, available: list[Position]) -> GeneratedMap:
        placements = self._rng.sample(available, k=self._entity_total())
        entities: dict[Position, EntityType] = {}
        cursor = 0
        for entity_type, count in self._entity_counts():
            entities.update(
                (position, entity_type)
                for position in placements[cursor : cursor + count]
            )
            cursor += count
        return GeneratedMap(self._config.rows, self._config.cols, entities)

    def _available_positions(self) -> list[Position]:
        self._validate_config()
        return [
            Position(row, col)
            for row in range(1, self._config.rows + 1)
            for col in range(1, self._config.cols + 1)
            if Position(row, col) not in protected_cells(
                self._config.rows, self._config.cols
            )
        ]

    def _entity_counts(self) -> tuple[tuple[EntityType, int], ...]:
        return (
            (EntityType.WUMPUS, self._config.wumpus_count),
            (EntityType.PIT, self._config.pit_count),
            (EntityType.GOLD, self._config.gold_count),
            (EntityType.BAT, self._config.bat_count),
        )

    def _entity_total(self) -> int:
        return sum(count for _, count in self._entity_counts())

    def _validate_config(self) -> None:
        if self._config.rows < 1 or self._config.cols < 1:
            raise MapGenerationError("Map dimensions must be positive")

        if any(
            not isinstance(count, int) or isinstance(count, bool) or count < 0
            for _, count in self._entity_counts()
        ):
            raise MapGenerationError(
                "Entity counts must be non-negative integers"
            )

        available_count = available_entity_cells(
            self._config.rows, self._config.cols
        )
        if self._entity_total() > available_count:
            raise MapGenerationError(
                "Entity count exceeds cells outside the initial safe zone"
            )

    def _validate_winnability_capacity(self) -> None:
        safe_component = self._safe_component_for_gold()
        hazards = (
            self._config.wumpus_count
            + self._config.pit_count
            + self._config.bat_count
        )
        if hazards > self._config.rows * self._config.cols - len(safe_component):
            raise MapGenerationError(
                "Esta combinação de entidades não permite gerar um mapa "
                "vencível para o objetivo selecionado."
            )

    def _random_route(self) -> tuple[Position, ...]:
        """Construct a seeded, varied orthogonal route from start to exit."""

        row, col = START_POSITION.row, START_POSITION.col
        route = [START_POSITION]
        while row != self._config.rows or col != self._config.cols:
            moves: list[tuple[int, int]] = []
            if row < self._config.rows:
                moves.append((1, 0))
            if col < self._config.cols:
                moves.append((0, 1))
            delta_row, delta_col = self._rng.choice(moves)
            row += delta_row
            col += delta_col
            route.append(Position(row, col))
        return tuple(route)

    def _safe_component_for_gold(self) -> set[Position]:
        safe_component = set(self._random_route()) | set(
            protected_cells(self._config.rows, self._config.cols)
        )
        protected = protected_cells(self._config.rows, self._config.cols)
        while len(safe_component.difference(protected)) < self._config.gold_count:
            candidates: set[Position] = set()
            for position in safe_component:
                for candidate in (
                    Position(position.row - 1, position.col),
                    Position(position.row + 1, position.col),
                    Position(position.row, position.col - 1),
                    Position(position.row, position.col + 1),
                ):
                    if candidate.is_inside(self._config.rows, self._config.cols):
                        candidates.add(candidate)
            candidates.difference_update(safe_component)
            if not candidates:
                raise MapGenerationError(
                    "Esta combinação de entidades não permite gerar um mapa "
                    "vencível para o objetivo selecionado."
                )
            safe_component.add(self._rng.choice(sorted(candidates)))
        return safe_component

    def _construct_winnable_map(self, available: list[Position]) -> GeneratedMap:
        safe_component = self._safe_component_for_gold()
        entities: dict[Position, EntityType] = {}
        remaining_hazard_slots = [
            position for position in available if position not in safe_component
        ]
        for entity_type, count in self._entity_counts():
            if entity_type is EntityType.GOLD:
                continue
            selected = self._rng.sample(remaining_hazard_slots, k=count)
            entities.update((position, entity_type) for position in selected)
            selected_set = set(selected)
            remaining_hazard_slots = [
                position for position in remaining_hazard_slots
                if position not in selected_set
            ]
        protected = protected_cells(self._config.rows, self._config.cols)
        gold_slots = sorted(safe_component.difference(protected))
        entities.update(
            (position, EntityType.GOLD)
            for position in self._rng.sample(gold_slots, k=self._config.gold_count)
        )
        generated_map = GeneratedMap(self._config.rows, self._config.cols, entities)
        if not is_winnable(generated_map, self._objective, self._config):
            raise AssertionError("Constructed map must satisfy the selected objective")
        return generated_map

    def _validate(self, generated_map: GeneratedMap) -> None:
        if (
            generated_map.rows != self._config.rows
            or generated_map.cols != self._config.cols
        ):
            raise AssertionError("Generated map dimensions do not match config")

        if any(
            not position.is_inside(generated_map.rows, generated_map.cols)
            for position in generated_map.entities
        ):
            raise AssertionError("Generated entity lies outside the map")

        if SAFE_INITIAL_CELLS.intersection(generated_map.entities):
            raise AssertionError("Generated entity lies in the initial safe zone")

        if self._config.exit_position in generated_map.entities:
            raise AssertionError("Generated entity lies in the protected exit")

        actual_counts = Counter(generated_map.entities.values())
        expected_counts = {
            entity_type: count
            for entity_type, count in self._entity_counts()
            if count
        }
        if actual_counts != expected_counts:
            raise AssertionError("Generated entity counts do not match config")

        if len(generated_map.entities) != self._entity_total():
            raise AssertionError("Generated entities overlap")

        if not is_winnable(generated_map, self._objective, self._config):
            raise AssertionError("Generated map is not winnable for its objective")
