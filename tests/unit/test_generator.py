import random
from collections import Counter

import pytest

from wumpus.domain import EntityType, Position
from wumpus.environment import (
    SAFE_INITIAL_CELLS,
    MapGenerationError,
    MapGenerator,
    is_world_solvable,
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


@pytest.mark.parametrize("seed", range(30))
def test_a_hazard_dense_config_stays_winnable_across_many_seeds(seed: int) -> None:
    """A tight, hazard-dense 6x6 config leaves little room to spare.

    16 hazards plus 3 gold out of 31 available cells makes it far more
    likely the bounded random-sampling phase needs several attempts (or the
    constructive fallback) before finding a layout where the exit and every
    gold stay reachable from the start -- exercising that path far harder
    than the spacious default config does.
    """

    config = GameConfig(rows=6, cols=6, wumpus_count=6, pit_count=6, gold_count=3, bat_count=4)
    generated_map = MapGenerator(rng=random.Random(seed), config=config).generate()

    assert is_world_solvable(generated_map)
    counts = Counter(generated_map.entities.values())
    assert counts[EntityType.WUMPUS] == 6
    assert counts[EntityType.PIT] == 6
    assert counts[EntityType.GOLD] == 3
    assert counts[EntityType.BAT] == 4
    assert not SAFE_INITIAL_CELLS.intersection(generated_map.entities)
    assert config.exit_position not in generated_map.entities


def test_constructive_fallback_alone_guarantees_exit_and_gold_reachability() -> None:
    """Directly exercise `_construct_winnable_map`, bypassing random sampling.

    Calling the constructive fallback directly proves it alone -- with no
    help from lucky random sampling -- always yields a map where the exit
    and every gold are reachable from the start.
    """

    config = GameConfig(rows=6, cols=6, wumpus_count=6, pit_count=6, gold_count=3, bat_count=4)
    for seed in range(20):
        generator = MapGenerator(rng=random.Random(seed), config=config)
        available = generator._available_positions()
        generated_map = generator._construct_winnable_map(available)

        assert is_world_solvable(generated_map)
        counts = Counter(generated_map.entities.values())
        assert counts[EntityType.WUMPUS] == 6
        assert counts[EntityType.PIT] == 6
        assert counts[EntityType.GOLD] == 3
        assert counts[EntityType.BAT] == 4
        assert not SAFE_INITIAL_CELLS.intersection(generated_map.entities)
        assert config.exit_position not in generated_map.entities
