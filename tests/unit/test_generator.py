import random
from collections import Counter

import pytest

from wumpus.domain import EntityType, Position
from wumpus.environment import (
    SAFE_INITIAL_CELLS,
    MapGenerationError,
    MapGenerator,
)
from wumpus.game import GameConfig


def generate(seed: int = 42, config: GameConfig | None = None):
    return MapGenerator(rng=random.Random(seed), config=config).generate()


def test_generator_creates_canonical_six_by_six_map() -> None:
    generated_map = generate()

    assert generated_map.rows == 6
    assert generated_map.cols == 6
    assert all(
        isinstance(generated_map.entity_at(Position(row, col)), EntityType)
        for row in range(1, 7)
        for col in range(1, 7)
    )


def test_generator_places_exact_entity_counts_without_overlap() -> None:
    generated_map = generate()

    assert Counter(generated_map.entities.values()) == {
        EntityType.WUMPUS: 2,
        EntityType.PIT: 4,
        EntityType.GOLD: 3,
        EntityType.BAT: 2,
    }
    assert len(generated_map.entities) == 11
    assert len(set(generated_map.entities)) == 11


@pytest.mark.parametrize("seed", range(20))
def test_generator_keeps_initial_zone_empty_for_multiple_seeds(seed: int) -> None:
    generated_map = generate(seed)

    assert SAFE_INITIAL_CELLS.isdisjoint(generated_map.entities)
    assert all(
        generated_map.entity_at(position) is EntityType.EMPTY
        for position in SAFE_INITIAL_CELLS
    )


def test_generator_is_deterministic_for_an_injected_seeded_rng() -> None:
    first = generate(seed=2026)
    second = generate(seed=2026)
    another_seed = generate(seed=2027)

    assert first == second
    assert first != another_seed


def test_generator_supports_valid_custom_configuration() -> None:
    config = GameConfig(
        rows=4,
        cols=5,
        wumpus_count=1,
        pit_count=2,
        gold_count=1,
        bat_count=1,
    )

    generated_map = generate(config=config)

    assert (generated_map.rows, generated_map.cols) == (4, 5)
    assert Counter(generated_map.entities.values()) == {
        EntityType.WUMPUS: 1,
        EntityType.PIT: 2,
        EntityType.GOLD: 1,
        EntityType.BAT: 1,
    }


@pytest.mark.parametrize(
    "config",
    [
        GameConfig(rows=0),
        GameConfig(pit_count=-1),
        GameConfig(
            rows=2,
            cols=2,
            wumpus_count=1,
            pit_count=1,
            gold_count=0,
            bat_count=0,
        ),
    ],
)
def test_generator_rejects_impossible_configuration(config: GameConfig) -> None:
    with pytest.raises(MapGenerationError):
        generate(config=config)


def test_generated_map_rejects_out_of_bounds_lookup() -> None:
    with pytest.raises(ValueError, match="outside generated map"):
        generate().entity_at(Position(0, 1))
