"""Deterministic presentation events derived only from observable results."""

import ast
from pathlib import Path

import pytest

from wumpus.domain import Action, ActionResult, Direction, Perception, Position
from wumpus.ui.retro_animation import (
    BANNER_EXIT_BLOCKED,
    FRAME_COUNTS,
    AnimationController,
    AnimationKind,
    build_turn_events,
    build_initial_sensor_events,
    expand_events,
    sensors_to_animate,
    shot_path,
)


def make_result(action: Action = Action.MOVE_FORWARD, **flags: bool) -> ActionResult:
    perception = flags.pop("perception", Perception(False, False, False, False, False, False))
    return ActionResult(
        action=action, position=Position(2, 1), direction=Direction.NORTH,
        score_delta=-1, total_score=-1, perception=perception, **flags,
    )


@pytest.mark.parametrize(
    ("attribute", "label"),
    (("stench", "FEDOR"), ("breeze", "BRISA"), ("bat_noise", "MORCEGO"),
     ("glitter", "BRILHO"), ("bump", "IMPACTO"), ("scream", "GRITO")),
)
def test_every_sensor_has_a_specific_visual_event(attribute: str, label: str) -> None:
    values = {name: False for name in ("stench", "breeze", "bat_noise", "glitter", "bump", "scream")}
    values[attribute] = True
    perception = Perception(**values)
    assert label in sensors_to_animate(perception, previous=None, entered_new_room=False)


def test_multiple_sensors_share_one_concurrent_frame_sequence() -> None:
    perception = Perception(True, True, True, False, False, False)
    events = build_turn_events(
        make_result(perception=perception), previous_position=Position(1, 1),
        previous_perception=None, bounds=(6, 6),
    )
    frames = expand_events(events)

    assert len(frames) == max(FRAME_COUNTS[AnimationKind.MOVE],
                              FRAME_COUNTS[AnimationKind.SENSORS])
    assert {label for label, _phase in frames[0].sensor_phases} == {
        "FEDOR", "BRISA", "MORCEGO"
    }


def test_initial_active_sensors_are_queued_after_the_intro_by_the_screen() -> None:
    events = build_initial_sensor_events(
        Perception(True, False, False, True, False, False)
    )
    assert len(events) == 1
    assert events[0].kind is AnimationKind.SENSORS
    assert events[0].sensors == ("FEDOR", "BRILHO")


@pytest.mark.parametrize(
    ("flags", "kind"),
    (({"teleported": True}, AnimationKind.TELEPORT),
     ({"gold_collected": True}, AnimationKind.GRAB),
     ({"died": True}, AnimationKind.DEATH),
     ({"escaped": True}, AnimationKind.ESCAPE),
     ({"exit_blocked": True}, AnimationKind.EXIT_BLOCKED),
     ({"wumpus_killed": True}, AnimationKind.WUMPUS_KILLED)),
)
def test_reported_special_results_create_their_specific_effect(
    flags: dict[str, bool], kind: AnimationKind
) -> None:
    result = make_result(Action.GRAB if "gold_collected" in flags else Action.MOVE_FORWARD, **flags)
    events = build_turn_events(
        result, previous_position=Position(1, 1), previous_perception=None,
        bounds=(6, 6),
    )
    assert kind in {event.kind for event in events}


def test_a_blocked_exit_warns_about_pending_gold_without_ending_the_game() -> None:
    """Reaching the exit too early is feedback, never a terminal result."""

    result = make_result(Action.MOVE_FORWARD, exit_blocked=True)
    events = build_turn_events(
        result, previous_position=Position(1, 1), previous_perception=None,
        bounds=(6, 6),
    )
    frames = expand_events(events)
    blocked = [
        frame for frame in frames if AnimationKind.EXIT_BLOCKED in frame.kinds
    ]

    assert len(blocked) == FRAME_COUNTS[AnimationKind.EXIT_BLOCKED]
    assert {frame.banner for frame in blocked} == {BANNER_EXIT_BLOCKED}
    assert "OURO PENDENTE" in BANNER_EXIT_BLOCKED
    # A warning flashes and clears; it must never be confused with an escape.
    assert AnimationKind.ESCAPE not in {event.kind for event in events}
    assert len({frame.border_flash for frame in blocked}) > 1


def test_the_escape_effect_plays_on_whatever_room_the_result_reports() -> None:
    """The victory room is the far-corner exit now, so nothing may assume [1,1]."""

    result = ActionResult(
        action=Action.MOVE_FORWARD, position=Position(6, 6), direction=Direction.NORTH,
        score_delta=-1, total_score=-1,
        perception=Perception(False, False, False, False, False, False),
        escaped=True,
    )
    events = build_turn_events(
        result, previous_position=Position(6, 5), previous_perception=None,
        bounds=(6, 6),
    )
    escape = [event for event in events if event.kind is AnimationKind.ESCAPE]

    assert [event.position for event in escape] == [Position(6, 6)]


def test_shot_animation_runs_to_the_wall_not_a_hidden_impact_coordinate() -> None:
    assert shot_path(Position(2, 2), Direction.EAST, (6, 6)) == tuple(
        Position(2, col) for col in range(3, 7)
    )


def test_controller_cancel_removes_current_and_queued_frames() -> None:
    controller = AnimationController()
    result = make_result()
    controller.enqueue(build_turn_events(
        result, previous_position=Position(1, 1), previous_perception=None,
        bounds=(6, 6),
    ))
    controller.advance()
    assert controller.busy
    controller.cancel()
    assert not controller.busy
    assert controller.frame is None


def test_lethal_teleport_keeps_teleport_drama_before_death() -> None:
    events = build_turn_events(
        make_result(teleported=True, died=True),
        previous_position=Position(1, 1), previous_perception=None,
        bounds=(6, 6),
    )
    assert tuple(event.kind for event in events[:2]) == (
        AnimationKind.TELEPORT,
        AnimationKind.DEATH,
    )


def test_animation_module_uses_no_rng_or_sleep() -> None:
    path = Path(__file__).parents[2] / "src/wumpus/ui/retro_animation.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name for alias in node.names]
            assert "random" not in names
            assert "time" not in names
        if isinstance(node, ast.Attribute):
            assert node.attr != "sleep"
