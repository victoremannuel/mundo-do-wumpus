"""Procedural generation of hidden Wumpus World maps."""

from __future__ import annotations

import random
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from wumpus.domain import EntityType, Position
from wumpus.game.config import (
    SAFE_INITIAL_CELLS,
    GameConfig,
    available_entity_cells,
    protected_cells,
)


__all__ = (
    "SAFE_INITIAL_CELLS",
    "GeneratedMap",
    "MapGenerationError",
    "MapGenerator",
)


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


class MapGenerator:
    """Generate maps using only the injected pseudo-random generator."""

    def __init__(
        self,
        rng: random.Random,
        config: GameConfig | None = None,
    ) -> None:
        self._rng = rng
        self._config = config if config is not None else GameConfig()

    def generate(self) -> GeneratedMap:
        """Generate one map and validate every structural invariant."""

        available = self._available_positions()
        placements = self._rng.sample(available, k=self._entity_total())
        entities: dict[Position, EntityType] = {}
        cursor = 0

        for entity_type, count in self._entity_counts():
            selected = placements[cursor : cursor + count]
            entities.update((position, entity_type) for position in selected)
            cursor += count

        generated_map = GeneratedMap(
            rows=self._config.rows,
            cols=self._config.cols,
            entities=entities,
        )
        self._validate(generated_map)
        return generated_map

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
