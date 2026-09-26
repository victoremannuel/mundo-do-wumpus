"""Tests for the persistent retro Textual interface.

The tests drive the real app through `App.run_test` and a `Pilot`, so they cover
the actual widget tree, bindings, and timer wiring rather than a stand-in. Each
test wraps its coroutine in `asyncio.run` instead of pulling in an async pytest
plugin.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import main
from wumpus.debug.retro_renderer import build_real_map_view
from wumpus.domain import Action, ActionResult, Direction, Perception, Position
from wumpus.game import GameEngine, GameStatus
from wumpus.ui.retro_animation import AnimationKind, build_turn_events, expand_events
from wumpus.ui.retro_app import (
    DUAL_MAP_MIN_WIDTH,
    DUAL_MAP_WITH_SIDEBAR_MIN_WIDTH,
    MAX_SPEED_INDEX,
    MIN_HEIGHT,
    MIN_WIDTH,
    STATE_FINISHED,
    STATE_PAUSED,
    STATE_RUNNING,
    AgentStatusWidget,
    DecisionWidget,
    EndGameOverlay,
    LegendWidget,
    PerceptionWidget,
    PixelMapWidget,
    RetroFooter,
    RetroGameApp,
    RetroHeader,
)

SEED = 42
BIG_TURN_BUDGET = 30


def build_app(
    *,
    seed: int = SEED,
    start_paused: bool = True,
    debug_enabled: bool = False,
    with_debug_source: bool = True,
    speed_index: int | None = None,
) -> tuple[RetroGameApp, GameEngine]:
    world, agent = main.build_game(seed)
    # UI tests exercise the real loop but use a small technical cap so a
    # fail-closed generated map cannot make an event-loop test slow.
    engine = GameEngine(world, agent, max_turns=BIG_TURN_BUDGET)
    kwargs: dict[str, Any] = {}
    if speed_index is not None:
        kwargs["speed_index"] = speed_index
    app = RetroGameApp(
        engine=engine,
        agent=agent,
        initial_observation=world.observation(),
        seed=seed,
        start_paused=start_paused,
        debug_enabled=debug_enabled,
        debug_map_source=(
            (lambda: build_real_map_view(world.debug_snapshot()))
            if with_debug_source
            else None
        ),
        **kwargs,
    )
    return app, engine


def drive(
    scenario: Callable[..., Awaitable[None]],
    *,
    size: tuple[int, int] = (MIN_WIDTH, MIN_HEIGHT),
    **app_options: Any,
) -> tuple[RetroGameApp, GameEngine]:
    """Run one app scenario headlessly and return the app and its engine."""

    app, engine = build_app(**app_options)

    async def runner() -> None:
        async with app.run_test(size=size) as pilot:
            await scenario(pilot, app, engine)

    asyncio.run(runner())
    return app, engine


async def step_until_over(pilot: Any, engine: GameEngine) -> None:
    for _ in range(BIG_TURN_BUDGET):
        if engine.is_over:
            return
        await pilot.press("n")


# ---------------------------------------------------------------------------
# Composition
# ---------------------------------------------------------------------------


def test_the_screen_mounts_every_fixed_panel_exactly_once() -> None:
    async def scenario(pilot: Any, app: RetroGameApp, _engine: GameEngine) -> None:
        for widget_type in (
            RetroHeader,
            AgentStatusWidget,
            PerceptionWidget,
            DecisionWidget,
            LegendWidget,
            RetroFooter,
            EndGameOverlay,
        ):
            assert len(app.screen.query(widget_type)) == 1, widget_type
        assert len(app.screen.query(PixelMapWidget)) == 2
        assert app.screen.query_one("#map-known", PixelMapWidget).display is True
        assert app.screen.query_one("#map-real", PixelMapWidget).display is False

    drive(scenario)


def test_the_widget_tree_stays_stable_across_many_turns() -> None:
    """A frame must update the existing widgets, never mount another screen."""

    async def scenario(pilot: Any, app: RetroGameApp, _engine: GameEngine) -> None:
        before = len(app.screen.query("*"))
        for _ in range(12):
            await pilot.press("n")
        after = len(app.screen.query("*"))

        assert after == before
        assert len(app.screen.query(PixelMapWidget)) == 2
        assert len(app.screen.query(AgentStatusWidget)) == 1
        assert len(app.screen.query(RetroFooter)) == 1

    drive(scenario)


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------


def test_pause_and_resume_toggle_the_execution_state() -> None:
    async def scenario(pilot: Any, app: RetroGameApp, _engine: GameEngine) -> None:
        assert app.state_label == STATE_RUNNING
        await pilot.press("p")
        assert app.paused is True
        assert app.state_label == STATE_PAUSED
        await pilot.press("p")
        assert app.paused is False
        assert app.state_label == STATE_RUNNING

    drive(scenario, start_paused=False, speed_index=0)


def test_step_advances_exactly_one_turn_and_leaves_the_game_paused() -> None:
    async def scenario(pilot: Any, app: RetroGameApp, engine: GameEngine) -> None:
        assert engine.turns == 0
        await pilot.press("n")
        assert engine.turns == 1
        assert app.state_label == STATE_PAUSED
        await pilot.press("n")
        assert engine.turns == 2
        assert app.paused is True

    drive(scenario)


def test_step_from_a_running_game_pauses_it_after_one_turn() -> None:
    async def scenario(pilot: Any, app: RetroGameApp, engine: GameEngine) -> None:
        await pilot.press("n")
        assert engine.turns == 1
        assert app.paused is True

    drive(scenario, start_paused=False, speed_index=0)


def test_debug_toggles_the_real_board_without_touching_the_known_one() -> None:
    async def scenario(pilot: Any, app: RetroGameApp, _engine: GameEngine) -> None:
        assert app.debug_enabled is False
        await pilot.press("d")
        assert app.debug_enabled is True
        assert app.screen.query_one("#map-real", PixelMapWidget).display is True
        await pilot.press("d")
        assert app.debug_enabled is False
        assert app.screen.query_one("#map-real", PixelMapWidget).display is False
        assert app.screen.query_one("#map-known", PixelMapWidget).display is True

    drive(scenario)


def test_debug_is_ignored_when_no_authorized_debug_source_was_injected() -> None:
    async def scenario(pilot: Any, app: RetroGameApp, _engine: GameEngine) -> None:
        await pilot.press("d")
        assert app.debug_enabled is False

    drive(scenario, with_debug_source=False, debug_enabled=True)


def test_speed_keys_move_inside_the_allowed_intervals_and_never_reach_zero() -> None:
    async def scenario(pilot: Any, app: RetroGameApp, _engine: GameEngine) -> None:
        start = app.speed_index
        await pilot.press("plus")
        assert app.speed_index == start + 1
        assert app.interval > 0
        await pilot.press("minus")
        assert app.speed_index == start
        for _ in range(10):
            await pilot.press("plus")
        assert app.speed_index == MAX_SPEED_INDEX
        assert app.interval > 0
        for _ in range(10):
            await pilot.press("minus")
        assert app.speed_index == 0
        assert app.interval > 0

    drive(scenario)


def test_quit_closes_the_application() -> None:
    async def scenario(pilot: Any, _app: RetroGameApp, _engine: GameEngine) -> None:
        await pilot.press("q")

    app, _engine = drive(scenario)

    assert app.is_running is False


def test_quit_after_the_game_reports_the_engine_outcome() -> None:
    async def scenario(pilot: Any, app: RetroGameApp, engine: GameEngine) -> None:
        await step_until_over(pilot, engine)
        await pilot.press("q")

    app, engine = drive(scenario)

    assert app.return_value is not None
    assert app.return_value == engine.outcome()


# ---------------------------------------------------------------------------
# End of game
# ---------------------------------------------------------------------------


def test_the_game_freezes_and_shows_the_summary_once_the_engine_is_over() -> None:
    async def scenario(pilot: Any, app: RetroGameApp, engine: GameEngine) -> None:
        await step_until_over(pilot, engine)

        assert engine.is_over
        assert app.finished is True
        assert app.state_label == STATE_FINISHED
        assert app.outcome is not None
        assert app.outcome.status in (
            GameStatus.ESCAPED,
            GameStatus.DEAD,
            GameStatus.TURN_LIMIT,
        )
        assert app.screen.query_one("#endgame", EndGameOverlay).display is True
        assert app.screen.query_one("#decision", DecisionWidget).display is False

        frozen = engine.turns
        await pilot.press("n")
        await pilot.press("p")
        assert engine.turns == frozen
        assert app.failure is None

    drive(scenario)


def test_the_summary_panel_shows_every_required_final_field() -> None:
    async def scenario(pilot: Any, app: RetroGameApp, engine: GameEngine) -> None:
        await step_until_over(pilot, engine)
        summary = app.screen.query_one("#endgame", EndGameOverlay).visual.plain

        for label in ("RESULT", "SCORE", "GOLD", "WUMPUS", "TURNS", "VISITED", "SEED"):
            assert label in summary
        assert str(engine.outcome().score) in summary
        assert str(SEED) in summary

    drive(scenario)


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------


def test_a_terminal_below_the_minimum_shows_a_notice_instead_of_crashing() -> None:
    async def scenario(pilot: Any, app: RetroGameApp, _engine: GameEngine) -> None:
        notice = app.screen.query_one("#overlay-too-small")
        assert notice.display is True
        assert "TERMINAL MUITO PEQUENO" in app.screen.query_one("#too-small").visual.plain

    drive(scenario, size=(95, 31))


def test_minimum_height_contains_legend_and_a_usable_decision_panel() -> None:
    async def scenario(_pilot: Any, app: RetroGameApp, _engine: GameEngine) -> None:
        screen = app.screen
        sidebar = screen.query_one("#sidebar")
        legend = screen.query_one("#legend", LegendWidget)
        decision = screen.query_one("#decision", DecisionWidget)
        assert screen.query_one("#overlay-too-small").display is False
        assert legend.region.y >= sidebar.content_region.y
        assert legend.region.bottom <= sidebar.content_region.bottom
        assert decision.content_region.height > 0
        assert legend.region.height >= 14
        board = screen.query_one("#map-known", PixelMapWidget).visual.plain
        assert board.count("INI") == 1 and board.count("SAI") == 0

    drive(scenario, size=(MIN_WIDTH, MIN_HEIGHT))


def test_one_row_below_the_minimum_never_leaves_a_clipped_layout() -> None:
    async def scenario(_pilot: Any, app: RetroGameApp, _engine: GameEngine) -> None:
        assert app.screen.query_one("#overlay-too-small").display is True

    drive(scenario, size=(MIN_WIDTH, MIN_HEIGHT - 1))


def test_resizing_recovers_the_layout_without_restarting_the_game() -> None:
    async def scenario(pilot: Any, app: RetroGameApp, engine: GameEngine) -> None:
        await pilot.press("n")
        await pilot.press("n")
        turns = engine.turns

        await pilot.resize_terminal(95, 31)
        await pilot.pause()
        assert app.screen.query_one("#overlay-too-small").display is True
        assert engine.turns == turns

        await pilot.resize_terminal(MIN_WIDTH, MIN_HEIGHT)
        await pilot.pause()
        assert app.screen.query_one("#overlay-too-small").display is False
        assert engine.turns == turns
        assert app.finished is False
        assert app.screen.query_one("#map-known", PixelMapWidget).visual.plain

    drive(scenario)


def test_a_real_textual_border_assignment_accepts_blocked_exit_with_breeze() -> None:
    async def scenario(_pilot: Any, app: RetroGameApp, _engine: GameEngine) -> None:
        result = ActionResult(
            action=Action.MOVE_FORWARD,
            position=Position(6, 6),
            direction=Direction.NORTH,
            score_delta=-1,
            total_score=-1,
            perception=Perception(False, True, False, False, False, False),
            exit_blocked=True,
        )
        screen = app.game_screen
        assert screen is not None
        frames = expand_events(build_turn_events(
            result,
            previous_position=Position(6, 5),
            previous_perception=None,
            bounds=(6, 6),
        ))
        combined = next(
            frame for frame in frames
            if {AnimationKind.EXIT_BLOCKED, AnimationKind.SENSORS}.issubset(frame.kinds)
        )
        screen.animation_controller.enqueue(() )
        screen._apply_frame_border(combined.border_flash)
        assert screen.failure is None

    drive(scenario)


def test_a_wide_terminal_in_debug_mode_shows_both_boards_at_full_scale() -> None:
    async def scenario(pilot: Any, app: RetroGameApp, _engine: GameEngine) -> None:
        await pilot.press("d")
        assert app.screen.query_one("#map-known", PixelMapWidget).display is True
        assert app.screen.query_one("#map-real", PixelMapWidget).display is True
        assert app.screen.query_one("#sidebar").display is True

    drive(scenario, size=(DUAL_MAP_WITH_SIDEBAR_MIN_WIDTH, MIN_HEIGHT))


def test_a_narrow_terminal_in_debug_mode_keeps_the_hud_and_promotes_the_real_board() -> None:
    async def scenario(pilot: Any, app: RetroGameApp, _engine: GameEngine) -> None:
        await pilot.press("d")
        assert app.screen.query_one("#map-real", PixelMapWidget).display is True
        assert app.screen.query_one("#map-known", PixelMapWidget).display is False
        assert app.screen.query_one("#sidebar").display is True

    drive(scenario, size=(MIN_WIDTH, MIN_HEIGHT))


def test_both_boards_fit_only_from_the_dual_map_threshold_upwards() -> None:
    assert DUAL_MAP_MIN_WIDTH > MIN_WIDTH
    assert DUAL_MAP_WITH_SIDEBAR_MIN_WIDTH >= DUAL_MAP_MIN_WIDTH


# ---------------------------------------------------------------------------
# Autonomy, determinism, and the anti-cheat boundary
# ---------------------------------------------------------------------------


def test_the_interface_does_not_change_the_game_a_bare_engine_would_play() -> None:
    async def scenario(pilot: Any, _app: RetroGameApp, engine: GameEngine) -> None:
        await step_until_over(pilot, engine)

    _app, engine = drive(scenario)
    through_interface = engine.outcome()

    world, agent = main.build_game(SEED)
    headless = GameEngine(world, agent, max_turns=BIG_TURN_BUDGET).run()

    assert through_interface == headless


def test_debug_observation_never_changes_the_agents_game() -> None:
    async def scenario(pilot: Any, _app: RetroGameApp, engine: GameEngine) -> None:
        await step_until_over(pilot, engine)

    _quiet_app, quiet_engine = drive(scenario)
    _loud_app, loud_engine = drive(scenario, debug_enabled=True)

    assert loud_engine.outcome() == quiet_engine.outcome()


def test_pausing_and_changing_speed_never_alters_the_outcome() -> None:
    async def scenario(pilot: Any, _app: RetroGameApp, engine: GameEngine) -> None:
        await pilot.press("n")
        await pilot.press("plus")
        await pilot.press("minus")
        await pilot.press("p")
        await pilot.press("p")
        await step_until_over(pilot, engine)

    _app, engine = drive(scenario)

    world, agent = main.build_game(SEED)
    assert engine.outcome() == GameEngine(world, agent, max_turns=BIG_TURN_BUDGET).run()


def test_the_interface_module_never_touches_a_random_source() -> None:
    """Visual randomness would consume entropy and break seed reproducibility."""

    import ast
    from pathlib import Path

    ui_package = Path(__file__).parents[2] / "src" / "wumpus" / "ui"
    modules = sorted(ui_package.glob("retro_*.py"))
    assert modules

    for module_path in modules:
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(alias.name != "random" for alias in node.names), module_path
            if isinstance(node, ast.ImportFrom):
                assert node.module != "random", module_path
            if isinstance(node, ast.Name):
                assert node.id not in {"random", "Random"}, module_path
            if isinstance(node, ast.Attribute):
                assert node.attr not in {"random", "randint", "choice", "shuffle"}, (
                    module_path
                )
