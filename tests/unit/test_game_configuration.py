"""Player-selected counts reuse the canonical generator configuration."""

import random
from collections import Counter

import pytest

import main
from wumpus.domain import EntityType
from wumpus.environment import MapGenerationError, MapGenerator
from wumpus.game import GameConfig, GameObjective
from wumpus.ui.retro_session import GameMode, SessionSettings, validate_cave


@pytest.mark.parametrize(
    "config",
    (GameConfig(), GameConfig(wumpus_count=1, pit_count=2, gold_count=5, bat_count=3),
     GameConfig(wumpus_count=0, pit_count=0, gold_count=0, bat_count=0)),
)
def test_generator_uses_exact_custom_counts(config: GameConfig) -> None:
    generated = MapGenerator(random.Random(42), config).generate()
    counts = Counter(generated.entities.values())
    assert counts[EntityType.WUMPUS] == config.wumpus_count
    assert counts[EntityType.PIT] == config.pit_count
    assert counts[EntityType.GOLD] == config.gold_count
    assert counts[EntityType.BAT] == config.bat_count


def test_more_than_32_entities_is_rejected_in_ui_and_generator() -> None:
    config = GameConfig(wumpus_count=33, pit_count=0, gold_count=0, bat_count=0)
    assert "32 células" in (validate_cave(config) or "")
    with pytest.raises(MapGenerationError, match="exceeds"):
        MapGenerator(random.Random(1), config).generate()


def test_build_game_remains_backward_compatible_and_accepts_config() -> None:
    default_world, _default_agent = main.build_game(42)
    custom = GameConfig(wumpus_count=1, pit_count=2, gold_count=5, bat_count=3)
    custom_world, custom_agent = main.build_game(42, custom)
    assert default_world.debug_snapshot().rows == custom_world.debug_snapshot().rows == 6
    assert custom_agent.strategy._total_gold == 5


def test_session_factory_selects_the_requested_agent_contract() -> None:
    manual = main.build_session(SessionSettings(GameMode.MANUAL, 42, GameConfig()))
    autonomous = main.build_session(SessionSettings(GameMode.AUTONOMOUS, 42, GameConfig()))
    assert manual.manual_action_submitter is not None
    assert autonomous.manual_action_submitter is None


def test_automatic_session_seed_is_concrete_and_restart_replays_the_map() -> None:
    settings = SessionSettings(
        GameMode.MANUAL,
        None,
        GameConfig(),
        objective=GameObjective.COLLECT_ALL_GOLD,
    )
    assert isinstance(settings.seed, int)
    first = main.build_session(settings)
    second = main.build_session(settings)
    assert first.settings.seed == settings.seed == second.settings.seed
    assert first.debug_map_source is not None and second.debug_map_source is not None
    assert first.debug_map_source().tiles == second.debug_map_source().tiles
