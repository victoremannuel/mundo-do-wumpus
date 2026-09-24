import random
from collections.abc import Mapping, Sequence

import pytest

from wumpus.domain import Action, Direction, EntityType, Position
from wumpus.environment import (
    BAT_CHAIN_LIMIT_EVENT,
    MAX_BAT_TELEPORT_CHAIN,
    BatTeleportError,
    GeneratedMap,
    World,
)


class ScriptedRandom(random.Random):
    def __init__(self, destinations: Sequence[Position]) -> None:
        super().__init__(0)
        self._destinations = iter(destinations)
        self.calls = 0

    def choice(self, sequence):
        destination = next(self._destinations)
        assert destination in sequence
        self.calls += 1
        return destination


def world_with(
    entities: Mapping[Position, EntityType],
    destinations: Sequence[Position],
    *,
    rows: int = 6,
    cols: int = 6,
) -> tuple[World, ScriptedRandom]:
    rng = ScriptedRandom(destinations)
    world = World(
        GeneratedMap(rows=rows, cols=cols, entities=entities),
        rng=rng,
    )
    return world, rng


def test_bat_teleports_with_injected_rng_and_remains_in_its_room() -> None:
    bat = Position(2, 1)
    world, rng = world_with(
        {bat: EntityType.BAT},
        [Position(1, 1), Position(3, 3)],
    )

    first = world.execute(Action.MOVE_FORWARD)
    second = world.execute(Action.MOVE_FORWARD)

    assert first.position == Position(1, 1)
    assert first.teleported is True
    assert second.position == Position(3, 3)
    assert second.teleported is True
    assert rng.calls == 2
    assert world.score == -2


def test_seeded_bat_teleport_is_reproducible() -> None:
    generated_map = GeneratedMap(
        rows=6,
        cols=6,
        entities={Position(2, 1): EntityType.BAT},
    )
    first = World(generated_map, rng=random.Random(2026))
    second = World(generated_map, rng=random.Random(2026))

    first_result = first.execute(Action.MOVE_FORWARD)
    second_result = second.execute(Action.MOVE_FORWARD)

    assert first_result.position == second_result.position
    assert first_result.teleported is True
    assert second_result.teleported is True


@pytest.mark.parametrize("hazard", [EntityType.PIT, EntityType.WUMPUS])
def test_bat_destination_resolves_lethal_hazard_immediately(
    hazard: EntityType,
) -> None:
    destination = Position(4, 4)
    world, _ = world_with(
        {
            Position(2, 1): EntityType.BAT,
            destination: hazard,
        },
        [destination],
    )

    result = world.execute(Action.MOVE_FORWARD)

    assert result.position == destination
    assert result.teleported is True
    assert result.died is True
    assert result.score_delta == -1001
    assert world.game_over is True


def test_bat_destination_resolves_gold_and_preserves_orientation() -> None:
    destination = Position(4, 4)
    world, _ = world_with(
        {
            Position(2, 1): EntityType.BAT,
            destination: EntityType.GOLD,
        },
        [destination],
    )

    result = world.execute(Action.MOVE_FORWARD)

    assert result.position == destination
    assert result.direction is Direction.NORTH
    assert result.perception.glitter is True
    assert result.gold_collected is False
    assert result.died is False


def test_bat_to_bat_triggers_another_teleport() -> None:
    second_bat = Position(3, 3)
    destination = Position(6, 6)
    world, rng = world_with(
        {
            Position(2, 1): EntityType.BAT,
            second_bat: EntityType.BAT,
        },
        [second_bat, destination],
    )

    result = world.execute(Action.MOVE_FORWARD)

    assert result.position == destination
    assert result.teleported is True
    assert result.direction is Direction.NORTH
    assert rng.calls == 2


def test_chain_limit_falls_back_to_a_non_bat_destination_and_records_event(
) -> None:
    bat = Position(2, 1)
    destination = Position(6, 6)
    world, rng = world_with(
        {bat: EntityType.BAT},
        [bat] * MAX_BAT_TELEPORT_CHAIN + [destination],
    )

    result = world.execute(Action.MOVE_FORWARD)

    assert result.position == destination
    assert result.teleported is True
    assert rng.calls == MAX_BAT_TELEPORT_CHAIN + 1
    assert world.last_event == BAT_CHAIN_LIMIT_EVENT


def test_chain_limit_raises_controlled_error_without_non_bat_destination(
) -> None:
    bats = {
        Position(1, 1): EntityType.BAT,
        Position(2, 1): EntityType.BAT,
    }
    world, _ = world_with(
        bats,
        [Position(2, 1)] * MAX_BAT_TELEPORT_CHAIN,
        rows=2,
        cols=1,
    )

    with pytest.raises(BatTeleportError, match="No non-bat"):
        world.execute(Action.MOVE_FORWARD)
