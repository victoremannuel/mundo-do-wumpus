import random
from collections.abc import Mapping

import pytest

from wumpus.domain import Action, Direction, EntityType, Position
from wumpus.environment import GeneratedMap, INVALID_CLIMB_EVENT, World
from wumpus.environment.scoring import DEATH_PENALTY, GOLD_REWARD, action_cost


def world_with(
    entities: Mapping[Position, EntityType] | None = None,
) -> World:
    return World(
        GeneratedMap(rows=6, cols=6, entities=entities or {}),
        rng=random.Random(0),
    )


def move_to_center(world: World, *, avoid_south: bool = False) -> None:
    if avoid_south:
        world.execute(Action.MOVE_FORWARD)
        world.execute(Action.MOVE_FORWARD)
        world.execute(Action.TURN_RIGHT)
        world.execute(Action.MOVE_FORWARD)
        world.execute(Action.MOVE_FORWARD)
        return

    world.execute(Action.TURN_RIGHT)
    world.execute(Action.MOVE_FORWARD)
    world.execute(Action.MOVE_FORWARD)
    world.execute(Action.TURN_LEFT)
    world.execute(Action.MOVE_FORWARD)
    world.execute(Action.MOVE_FORWARD)


def test_world_starts_at_exit_facing_north_with_zero_score() -> None:
    world = world_with()

    assert world.agent_position == Position(1, 1)
    assert world.agent_direction is Direction.NORTH
    assert world.score == 0
    assert world.collected_gold == 0
    assert world.game_over is False
    assert world.escaped is False
    assert world.dead is False


@pytest.mark.parametrize(
    ("entity_type", "signal"),
    [
        (EntityType.WUMPUS, "stench"),
        (EntityType.PIT, "breeze"),
        (EntityType.BAT, "bat_noise"),
    ],
)
@pytest.mark.parametrize(
    ("hazard", "avoid_south"),
    [
        (Position(4, 3), False),
        (Position(3, 4), False),
        (Position(2, 3), True),
        (Position(3, 2), False),
    ],
)
def test_sensors_detect_orthogonally_adjacent_entities(
    entity_type: EntityType,
    signal: str,
    hazard: Position,
    avoid_south: bool,
) -> None:
    world = world_with({hazard: entity_type})
    move_to_center(world, avoid_south=avoid_south)

    assert getattr(world.observe(), signal) is True


@pytest.mark.parametrize(
    ("entity_type", "signal"),
    [
        (EntityType.WUMPUS, "stench"),
        (EntityType.PIT, "breeze"),
        (EntityType.BAT, "bat_noise"),
    ],
)
def test_sensors_ignore_diagonal_entities(
    entity_type: EntityType, signal: str
) -> None:
    world = world_with({Position(4, 4): entity_type})
    move_to_center(world)

    assert getattr(world.observe(), signal) is False


def test_glitter_exists_only_in_the_gold_room() -> None:
    local_gold = world_with({Position(1, 1): EntityType.GOLD})
    adjacent_gold = world_with({Position(1, 2): EntityType.GOLD})

    assert local_gold.observe().glitter is True
    assert adjacent_gold.observe().glitter is False


def test_wall_collision_preserves_position_and_emits_one_bump() -> None:
    world = world_with()
    world.execute(Action.TURN_LEFT)

    result = world.execute(Action.MOVE_FORWARD)

    assert result.position == Position(1, 1)
    assert result.perception.bump is True
    assert result.score_delta == -1
    assert result.total_score == -2
    assert world.observe().bump is False


def test_right_and_left_rotations_complete_their_cycles() -> None:
    right_world = world_with()
    left_world = world_with()

    assert right_world.execute(Action.TURN_RIGHT).direction is Direction.EAST
    assert left_world.execute(Action.TURN_LEFT).direction is Direction.WEST
    for _ in range(3):
        right_world.execute(Action.TURN_RIGHT)
        left_world.execute(Action.TURN_LEFT)

    assert right_world.agent_direction is Direction.NORTH
    assert left_world.agent_direction is Direction.NORTH
    assert right_world.score == -4
    assert left_world.score == -4


@pytest.mark.parametrize("entity_type", [EntityType.PIT, EntityType.WUMPUS])
def test_entering_a_lethal_hazard_ends_game(entity_type: EntityType) -> None:
    world = world_with({Position(2, 1): entity_type})

    result = world.execute(Action.MOVE_FORWARD)

    assert result.position == Position(2, 1)
    assert result.score_delta == -1001
    assert result.total_score == -1001
    assert result.died is True
    assert world.dead is True
    assert world.game_over is True
    with pytest.raises(RuntimeError, match="after the game ends"):
        world.execute(Action.TURN_RIGHT)


def test_grab_collects_and_removes_gold_with_combined_score() -> None:
    world = world_with({Position(1, 1): EntityType.GOLD})

    result = world.execute(Action.GRAB)

    assert result.gold_collected is True
    assert result.score_delta == 999
    assert result.total_score == 999
    assert result.perception.glitter is False
    assert world.collected_gold == 1

    second_result = world.execute(Action.GRAB)
    assert second_result.gold_collected is False
    assert second_result.score_delta == -1
    assert world.collected_gold == 1


def test_climb_escapes_only_from_start_position() -> None:
    at_exit = world_with()
    away_from_exit = world_with()

    escaped = at_exit.execute(Action.CLIMB)
    away_from_exit.execute(Action.MOVE_FORWARD)
    did_not_escape = away_from_exit.execute(Action.CLIMB)

    assert escaped.escaped is True
    assert escaped.total_score == -1
    assert at_exit.game_over is True
    assert did_not_escape.escaped is False
    assert away_from_exit.game_over is False
    assert away_from_exit.score == -2
    assert away_from_exit.last_event == INVALID_CLIMB_EVENT


def test_scoring_rules_have_one_canonical_source() -> None:
    assert action_cost(Action.MOVE_FORWARD) == -1
    assert action_cost(Action.TURN_RIGHT) == -1
    assert action_cost(Action.TURN_LEFT) == -1
    assert action_cost(Action.GRAB) == -1
    assert action_cost(Action.CLIMB) == -1
    assert action_cost(Action.SHOOT) == -10
    assert GOLD_REWARD == 1000
    assert DEATH_PENALTY == -1000


def test_world_does_not_publish_hidden_map_collections() -> None:
    world = world_with({Position(2, 1): EntityType.WUMPUS})

    assert not hasattr(world, "entities")
    assert not hasattr(world, "wumpus_positions")
    assert not hasattr(world, "pit_positions")
    assert not hasattr(world, "bat_positions")
    assert not hasattr(world, "gold_positions")
