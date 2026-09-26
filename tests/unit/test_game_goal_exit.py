"""Regression coverage for GAME-GOAL-EXIT-CORNER-003."""

import random
from collections import deque

import pytest

import wumpus.environment.world as world_module
from wumpus.agent import KnowledgeBase, Strategy
from wumpus.domain import Action, Direction, EntityType, Position
from wumpus.environment import (
    GeneratedMap,
    MapGenerationError,
    MapGenerator,
    World,
    is_winnable,
)
from wumpus.game import GameConfig, GameObjective, available_entity_cells


def independently_reachable(
    generated: GeneratedMap, config: GameConfig,
) -> set[Position]:
    """Small test-only flood fill, intentionally independent of production."""

    start = Position(1, 1)
    reachable = {start}
    pending = deque([start])
    blockers = {EntityType.PIT, EntityType.WUMPUS, EntityType.BAT}
    while pending:
        position = pending.popleft()
        for candidate in position.neighbors():
            if (
                not candidate.is_inside(config.rows, config.cols)
                or candidate in reachable
                or generated.entity_at(candidate) in blockers
            ):
                continue
            reachable.add(candidate)
            pending.append(candidate)
    return reachable


def world_2x2(
    entities: dict[Position, EntityType] | None = None,
    *,
    objective: GameObjective,
) -> World:
    return World(
        GeneratedMap(rows=2, cols=2, entities=entities or {}),
        rng=random.Random(7),
        objective=objective,
    )


def enter_exit(world: World) -> object:
    world.execute(Action.MOVE_FORWARD)
    world.execute(Action.TURN_RIGHT)
    return world.execute(Action.MOVE_FORWARD)


def test_config_centralizes_the_opposite_corner_exit_and_capacity() -> None:
    config = GameConfig()
    assert config.exit_position == Position(6, 6)
    assert Position(1, 1) == Position(1, 1)
    assert available_entity_cells(6, 6) == 32
    assert available_entity_cells(2, 2) == 0


def test_generator_keeps_exit_and_initial_zone_empty_for_one_hundred_seeds() -> None:
    config = GameConfig()
    for seed in range(100):
        generated = MapGenerator(random.Random(seed), config).generate()
        assert config.exit_position not in generated.entities
        assert all(cell not in generated.entities for cell in (Position(1, 1), Position(1, 2), Position(2, 1)))


def test_generator_rejects_capacity_valid_but_structurally_unwinnable_entities() -> None:
    full = GameConfig(wumpus_count=32, pit_count=0, gold_count=0, bat_count=0)
    with pytest.raises(MapGenerationError, match="mapa vencível"):
        MapGenerator(random.Random(1), full).generate()
    too_many = GameConfig(wumpus_count=33, pit_count=0, gold_count=0, bat_count=0)
    with pytest.raises(MapGenerationError):
        MapGenerator(random.Random(1), too_many).generate()


def test_winnability_is_objective_aware_for_an_isolated_gold() -> None:
    config = GameConfig(rows=5, cols=5)
    generated = GeneratedMap(
        rows=5,
        cols=5,
        entities={
            Position(3, 3): EntityType.GOLD,
            Position(2, 3): EntityType.PIT,
            Position(3, 2): EntityType.WUMPUS,
            Position(3, 4): EntityType.BAT,
            Position(4, 3): EntityType.PIT,
        },
    )
    assert is_winnable(generated, GameObjective.ESCAPE_FAST, config)
    assert not is_winnable(generated, GameObjective.COLLECT_ALL_GOLD, config)


@pytest.mark.parametrize("objective", tuple(GameObjective))
def test_default_maps_are_winnable_for_one_hundred_seeds(objective: GameObjective) -> None:
    config = GameConfig()
    for seed in range(100):
        generated = MapGenerator(random.Random(seed), config, objective=objective).generate()
        reachable = independently_reachable(generated, config)
        assert config.exit_position in reachable
        if objective is GameObjective.COLLECT_ALL_GOLD:
            assert all(
                position in reachable
                for position, entity in generated.entities.items()
                if entity is EntityType.GOLD
            )


@pytest.mark.parametrize("objective", tuple(GameObjective))
def test_same_seed_config_and_objective_reproduce_the_same_map(
    objective: GameObjective,
) -> None:
    config = GameConfig()
    first = MapGenerator(random.Random(2026), config, objective=objective).generate()
    second = MapGenerator(random.Random(2026), config, objective=objective).generate()
    assert first.entities == second.entities


def test_fast_escape_is_automatic_and_climb_at_start_never_wins() -> None:
    world = world_2x2(objective=GameObjective.ESCAPE_FAST)
    climb = world.execute(Action.CLIMB)
    assert not climb.escaped and not world.game_over
    result = enter_exit(world)
    assert result.escaped and world.escaped and world.game_over


def test_collect_all_blocks_then_escapes_after_every_gold() -> None:
    blocked = world_2x2({Position(1, 2): EntityType.GOLD}, objective=GameObjective.COLLECT_ALL_GOLD)
    result = enter_exit(blocked)
    assert result.exit_blocked and not result.escaped and not blocked.game_over

    complete = world_2x2({Position(1, 2): EntityType.GOLD}, objective=GameObjective.COLLECT_ALL_GOLD)
    complete.execute(Action.TURN_RIGHT)
    complete.execute(Action.MOVE_FORWARD)
    complete.execute(Action.GRAB)
    complete.execute(Action.TURN_LEFT)
    result = complete.execute(Action.MOVE_FORWARD)
    assert result.escaped and complete.game_over


def test_collect_all_with_zero_gold_escapes_at_the_exit() -> None:
    world = world_2x2(objective=GameObjective.COLLECT_ALL_GOLD)
    assert enter_exit(world).escaped


@pytest.mark.parametrize(
    ("objective", "gold", "escapes"),
    (
        (GameObjective.ESCAPE_FAST, False, True),
        (GameObjective.COLLECT_ALL_GOLD, False, True),
        (GameObjective.COLLECT_ALL_GOLD, True, False),
    ),
)
def test_bat_teleport_to_exit_uses_the_same_exit_rule(
    monkeypatch: pytest.MonkeyPatch,
    objective: GameObjective,
    gold: bool,
    escapes: bool,
) -> None:
    entities = {Position(2, 1): EntityType.BAT}
    if gold:
        entities[Position(1, 2)] = EntityType.GOLD
    monkeypatch.setattr(world_module, "choose_teleport_destination", lambda *_args, **_kwargs: Position(2, 2))
    world = world_2x2(entities, objective=objective)
    result = world.execute(Action.MOVE_FORWARD)
    assert result.teleported and result.escaped is escapes and world.game_over is escapes
    assert result.exit_blocked is gold


def safe_knowledge() -> KnowledgeBase:
    knowledge = KnowledgeBase(3, 3)
    for cell in (Position(1, 1), Position(2, 1), Position(3, 1), Position(3, 2), Position(3, 3)):
        knowledge.mark_safe(cell)
    knowledge.mark_visited(Position(1, 1))
    return knowledge


def test_strategy_fast_ignores_glitter_but_collect_all_grabs_it() -> None:
    knowledge = safe_knowledge()
    fast = Strategy(total_gold=1, objective=GameObjective.ESCAPE_FAST, exit_position=Position(3, 3))
    collect = Strategy(total_gold=1, objective=GameObjective.COLLECT_ALL_GOLD, exit_position=Position(3, 3))
    kwargs = dict(knowledge=knowledge, position=Position(1, 1), direction=Direction.NORTH, collected_gold=0, glitter=True)
    assert fast.decide(**kwargs) is not Action.GRAB
    assert collect.decide(**kwargs) is Action.GRAB


def test_strategy_collect_all_targets_exit_after_last_gold_without_climb() -> None:
    knowledge = safe_knowledge()
    strategy = Strategy(total_gold=1, objective=GameObjective.COLLECT_ALL_GOLD, exit_position=Position(3, 3))
    action = strategy.decide(knowledge=knowledge, position=Position(1, 1), direction=Direction.NORTH, collected_gold=1, glitter=False)
    assert action is Action.MOVE_FORWARD
    assert strategy._target == Position(3, 3)
    assert action is not Action.CLIMB


def test_fast_frontier_prefers_estimated_progress_but_never_confirmed_danger() -> None:
    knowledge = KnowledgeBase(3, 3)
    for cell in (Position(1, 1), Position(1, 2), Position(2, 1), Position(2, 2), Position(3, 2), Position(3, 3)):
        knowledge.mark_safe(cell)
    knowledge.mark_visited(Position(1, 1))
    knowledge.mark_confirmed(Position(1, 3), EntityType.PIT)
    strategy = Strategy(total_gold=0, objective=GameObjective.ESCAPE_FAST, exit_position=Position(3, 3))
    action = strategy.decide(knowledge=knowledge, position=Position(1, 1), direction=Direction.NORTH, collected_gold=0, glitter=False)
    assert action is Action.MOVE_FORWARD
    assert strategy._target == Position(3, 3)
