from dataclasses import FrozenInstanceError, fields

import pytest

from wumpus.domain import (
    Action,
    ActionResult,
    Direction,
    EntityType,
    Perception,
    Position,
)
from wumpus.game import GameConfig


def test_domain_enums_have_the_plan_defined_members() -> None:
    assert [member.name for member in Direction] == [
        "NORTH",
        "EAST",
        "SOUTH",
        "WEST",
    ]
    assert [member.name for member in Action] == [
        "MOVE_FORWARD",
        "TURN_RIGHT",
        "TURN_LEFT",
        "GRAB",
        "SHOOT",
        "CLIMB",
    ]
    assert [member.name for member in EntityType] == [
        "EMPTY",
        "WUMPUS",
        "PIT",
        "GOLD",
        "BAT",
    ]


def test_position_is_an_immutable_ordered_value_object() -> None:
    position = Position(2, 3)

    assert position == Position(2, 3)
    assert hash(position) == hash(Position(2, 3))
    assert sorted([Position(2, 1), Position(1, 6)]) == [
        Position(1, 6),
        Position(2, 1),
    ]
    with pytest.raises(FrozenInstanceError):
        position.row = 4  # type: ignore[misc]


def test_position_exposes_orthogonal_neighbors() -> None:
    assert set(Position(2, 2).neighbors()) == {
        Position(3, 2),
        Position(2, 3),
        Position(1, 2),
        Position(2, 1),
    }


@pytest.mark.parametrize(
    ("position", "expected"),
    [
        (Position(1, 1), True),
        (Position(6, 6), True),
        (Position(0, 1), False),
        (Position(1, 0), False),
        (Position(7, 6), False),
        (Position(6, 7), False),
    ],
)
def test_position_uses_one_based_world_bounds(
    position: Position, expected: bool
) -> None:
    assert position.is_inside(rows=6, cols=6) is expected


def test_position_calculates_manhattan_distance() -> None:
    assert Position(1, 1).manhattan_distance(Position(4, 5)) == 7
    assert Position(4, 5).manhattan_distance(Position(1, 1)) == 7
    assert Position(3, 3).manhattan_distance(Position(3, 3)) == 0


def test_perception_has_exactly_six_immutable_signals() -> None:
    perception = Perception(
        stench=True,
        breeze=False,
        bat_noise=True,
        glitter=False,
        bump=True,
        scream=False,
    )

    assert [field.name for field in fields(Perception)] == [
        "stench",
        "breeze",
        "bat_noise",
        "glitter",
        "bump",
        "scream",
    ]
    with pytest.raises(FrozenInstanceError):
        perception.bump = False  # type: ignore[misc]


def test_action_result_records_outcome_with_false_event_defaults() -> None:
    perception = Perception(False, False, False, False, False, False)
    result = ActionResult(
        action=Action.MOVE_FORWARD,
        position=Position(1, 2),
        direction=Direction.EAST,
        score_delta=-1,
        total_score=-1,
        perception=perception,
    )

    assert result.action is Action.MOVE_FORWARD
    assert result.position == Position(1, 2)
    assert result.direction is Direction.EAST
    assert result.score_delta == -1
    assert result.total_score == -1
    assert result.perception is perception
    assert result.gold_collected is False
    assert result.wumpus_killed is False
    assert result.teleported is False
    assert result.died is False
    assert result.escaped is False


def test_game_config_uses_canonical_defaults_and_remains_configurable() -> None:
    assert GameConfig() == GameConfig(
        rows=6,
        cols=6,
        wumpus_count=2,
        pit_count=4,
        gold_count=3,
        bat_count=2,
    )
    assert GameConfig(rows=8, cols=7).rows == 8
