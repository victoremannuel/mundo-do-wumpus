import random
from collections.abc import Mapping

import pytest

from wumpus.domain import Action, Direction, EntityType, Position
from wumpus.environment import GeneratedMap, World


def world_with(entities: Mapping[Position, EntityType]) -> World:
    return World(
        GeneratedMap(rows=6, cols=6, entities=entities),
        rng=random.Random(0),
    )


def test_arrow_kills_wumpus_in_same_column() -> None:
    world = world_with({Position(4, 1): EntityType.WUMPUS})

    result = world.execute(Action.SHOOT)

    assert result.wumpus_killed is True
    assert result.position == Position(1, 1)
    assert result.direction is Direction.NORTH
    assert world.killed_wumpus == 1


def test_arrow_kills_wumpus_in_same_row() -> None:
    world = world_with({Position(1, 4): EntityType.WUMPUS})
    world.execute(Action.TURN_RIGHT)

    result = world.execute(Action.SHOOT)

    assert result.wumpus_killed is True
    assert result.direction is Direction.EAST


def test_arrow_does_not_hit_wumpus_behind_agent() -> None:
    world = world_with({Position(2, 1): EntityType.WUMPUS})
    world.execute(Action.TURN_RIGHT)
    world.execute(Action.TURN_RIGHT)

    result = world.execute(Action.SHOOT)

    assert world.agent_direction is Direction.SOUTH
    assert result.wumpus_killed is False
    assert world.killed_wumpus == 0


def test_arrow_does_not_hit_wumpus_outside_line_of_fire() -> None:
    world = world_with({Position(2, 2): EntityType.WUMPUS})

    result = world.execute(Action.SHOOT)

    assert result.wumpus_killed is False
    assert world.killed_wumpus == 0


def test_arrow_hits_only_first_live_wumpus_and_dead_cell_is_transitable() -> None:
    world = world_with(
        {
            Position(2, 1): EntityType.WUMPUS,
            Position(4, 1): EntityType.WUMPUS,
        }
    )

    first_shot = world.execute(Action.SHOOT)
    movement = world.execute(Action.MOVE_FORWARD)
    second_shot = world.execute(Action.SHOOT)

    assert first_shot.wumpus_killed is True
    assert movement.position == Position(2, 1)
    assert movement.died is False
    assert world.dead is False
    assert second_shot.wumpus_killed is True
    assert world.killed_wumpus == 2


@pytest.mark.parametrize(
    ("entities", "expected_kill"),
    [
        ({Position(3, 1): EntityType.WUMPUS}, True),
        ({Position(3, 2): EntityType.WUMPUS}, False),
    ],
)
def test_shoot_cost_is_exactly_minus_ten(
    entities: Mapping[Position, EntityType], expected_kill: bool
) -> None:
    world = world_with(entities)

    result = world.execute(Action.SHOOT)

    assert result.score_delta == -10
    assert result.total_score == -10
    assert result.wumpus_killed is expected_kill


def test_scream_is_emitted_once_and_stench_updates_after_kill() -> None:
    world = world_with({Position(2, 1): EntityType.WUMPUS})
    assert world.observe().stench is True

    result = world.execute(Action.SHOOT)

    assert result.perception.scream is True
    assert result.perception.stench is False
    assert world.observe().scream is False
    assert world.observe().stench is False


def test_arrows_are_unlimited_and_misses_do_not_end_game() -> None:
    world = world_with({})

    results = [world.execute(Action.SHOOT) for _ in range(5)]

    assert all(result.wumpus_killed is False for result in results)
    assert world.score == -50
    assert world.game_over is False
