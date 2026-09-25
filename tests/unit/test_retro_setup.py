"""Textual setup, manual controls, and restart lifecycle."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from textual.widgets import Button, Input

import main
from wumpus.domain import Action
from wumpus.game import GameEngine
from wumpus.ui.retro_animation import build_intro_events
from wumpus.ui.retro_app import GameScreen, MIN_HEIGHT, MIN_WIDTH, RetroGameApp
from wumpus.ui.retro_session import GameMode, SessionSettings
from wumpus.ui.retro_setup import SetupScreen
from wumpus.ui.retro_tiles import TileKind


def run_scenario(scenario: Any) -> None:
    app = RetroGameApp(
        session_factory=main.build_session,
        seed=42,
        start_paused=True,
    )

    async def runner() -> None:
        async with app.run_test(size=(MIN_WIDTH, MIN_HEIGHT)) as pilot:
            await scenario(pilot, app)

    asyncio.run(runner())


def test_setup_appears_first_with_defaults_and_no_selected_mode() -> None:
    async def scenario(pilot: Any, app: RetroGameApp) -> None:
        assert isinstance(app.screen, SetupScreen)
        assert app.game_screen is None
        assert app.screen.query_one("#start-game", Button).disabled
        assert [
            app.screen.query_one(f"#{field}", Input).value
            for field in ("wumpus-count", "pit-count", "gold-count", "bat-count")
        ] == ["2", "4", "3", "2"]

    run_scenario(scenario)


def test_number_then_enter_starts_from_the_focused_mode_selector() -> None:
    async def scenario(pilot: Any, app: RetroGameApp) -> None:
        assert isinstance(app.screen, SetupScreen)
        await pilot.press("1", "enter")
        await pilot.pause()
        assert isinstance(app.screen, GameScreen)
        assert app.game_screen is not None
        assert app.game_screen.session.mode is GameMode.AUTONOMOUS

    run_scenario(scenario)


def test_mode_shortcuts_do_not_capture_digits_typed_in_count_inputs() -> None:
    async def scenario(pilot: Any, app: RetroGameApp) -> None:
        setup = app.screen
        assert isinstance(setup, SetupScreen)
        field = setup.query_one("#wumpus-count", Input)
        field.value = ""
        field.focus()
        await pilot.press("1")
        assert field.value == "1"
        assert setup.selected_mode is None

    run_scenario(scenario)


def test_quit_works_even_while_a_count_input_has_focus() -> None:
    app = RetroGameApp(session_factory=main.build_session, seed=42)

    async def runner() -> None:
        async with app.run_test(size=(MIN_WIDTH, MIN_HEIGHT)) as pilot:
            app.screen.query_one("#wumpus-count", Input).focus()
            await pilot.press("q")

    asyncio.run(runner())
    assert not app.is_running


def test_invalid_capacity_stays_on_setup_and_shows_a_readable_error() -> None:
    async def scenario(_pilot: Any, app: RetroGameApp) -> None:
        setup = app.screen
        assert isinstance(setup, SetupScreen)
        setup.action_select_autonomous()
        setup.query_one("#wumpus-count", Input).value = "34"
        setup.query_one("#pit-count", Input).value = "0"
        setup.query_one("#gold-count", Input).value = "0"
        setup.query_one("#bat-count", Input).value = "0"
        setup.action_start_game()
        assert isinstance(app.screen, SetupScreen)
        error = setup.query_one("#setup-error").visual.plain
        assert "CONFIGURAÇÃO INVÁLIDA" in error
        assert "33 células" in error

    run_scenario(scenario)


def test_valid_selection_reaches_the_requested_session_and_custom_counts() -> None:
    async def scenario(pilot: Any, app: RetroGameApp) -> None:
        setup = app.screen
        assert isinstance(setup, SetupScreen)
        setup.action_select_autonomous()
        for field, value in (("wumpus-count", "1"), ("pit-count", "2"),
                             ("gold-count", "5"), ("bat-count", "3")):
            setup.query_one(f"#{field}", Input).value = value
        setup.action_start_game()
        await pilot.pause()
        assert isinstance(app.screen, GameScreen)
        assert app.game_screen is not None
        assert app.game_screen.session.mode is GameMode.AUTONOMOUS
        config = app.game_screen.session.settings.config
        assert (config.wumpus_count, config.pit_count,
                config.gold_count, config.bat_count) == (1, 2, 5, 3)
        source = app.game_screen.session.debug_map_source
        assert source is not None
        kinds = tuple(source().tiles.values())
        assert kinds.count(TileKind.WUMPUS) == 1
        assert kinds.count(TileKind.PIT) == 2
        assert kinds.count(TileKind.GOLD) == 5
        assert kinds.count(TileKind.BAT) == 3

    run_scenario(scenario)


def test_manual_mode_never_advances_without_a_player_command() -> None:
    async def scenario(pilot: Any, app: RetroGameApp) -> None:
        setup = app.screen
        assert isinstance(setup, SetupScreen)
        setup.action_select_manual()
        setup.action_start_game()
        await pilot.pause(1.0)
        assert app.game_screen is not None
        assert app.game_screen.session.engine.turns == 0
        assert app.game_screen.state_label == "JOGADOR"

    run_scenario(scenario)


@pytest.mark.parametrize(
    ("key", "action"),
    (("up", Action.MOVE_FORWARD), ("left", Action.TURN_LEFT),
     ("right", Action.TURN_RIGHT), ("g", Action.GRAB),
     ("f", Action.SHOOT), ("e", Action.CLIMB)),
)
def test_each_manual_key_executes_exactly_one_engine_turn(key: str, action: Action) -> None:
    async def scenario(pilot: Any, app: RetroGameApp) -> None:
        setup = app.screen
        assert isinstance(setup, SetupScreen)
        setup.action_select_manual()
        setup.action_start_game()
        await pilot.pause(1.0)
        game = app.game_screen
        assert game is not None
        await pilot.press(key)
        assert game.session.engine.turns == 1
        assert game.session.presentation_source.memory.actions == (action,)

    run_scenario(scenario)


def test_manual_commands_are_ignored_while_the_previous_action_animates() -> None:
    async def scenario(pilot: Any, app: RetroGameApp) -> None:
        setup = app.screen
        assert isinstance(setup, SetupScreen)
        setup.action_select_manual()
        setup.action_start_game()
        await pilot.pause(1.0)
        game = app.game_screen
        assert game is not None
        await pilot.press("left")
        assert game.session.engine.turns == 1
        assert game.animation_controller.busy
        await pilot.press("right")
        assert game.session.engine.turns == 1

    run_scenario(scenario)


def test_restart_during_animation_cancels_the_old_session_and_preserves_settings() -> None:
    async def scenario(pilot: Any, app: RetroGameApp) -> None:
        setup = app.screen
        assert isinstance(setup, SetupScreen)
        setup.action_select_autonomous()
        setup.action_start_game()
        await pilot.pause()
        old_game = app.game_screen
        assert old_game is not None
        old_engine = old_game.session.engine
        assert old_game.animation_controller.busy

        await pilot.press("r")
        assert isinstance(app.screen, SetupScreen)
        assert app.screen.selected_mode is GameMode.AUTONOMOUS
        assert app.screen.query_one("#wumpus-count", Input).value == "2"
        await pilot.pause(1.0)
        assert old_engine.turns == 0
        assert not old_game.animation_controller.busy

        app.screen.action_start_game()
        await pilot.pause()
        assert app.game_screen is not None
        assert app.game_screen.session.engine is not old_engine
        assert app.game_screen.session.engine.turns == 0

    run_scenario(scenario)


def test_restart_also_works_after_game_over() -> None:
    async def scenario(pilot: Any, app: RetroGameApp) -> None:
        setup = app.screen
        assert isinstance(setup, SetupScreen)
        setup.action_select_manual()
        setup.action_start_game()
        await pilot.pause(1.0)
        await pilot.press("e")
        await pilot.pause(0.7)
        assert app.game_screen is not None and app.game_screen.finished
        await pilot.press("r")
        assert isinstance(app.screen, SetupScreen)

    run_scenario(scenario)


def test_fifty_animation_frames_keep_the_widget_tree_stable() -> None:
    async def scenario(pilot: Any, app: RetroGameApp) -> None:
        setup = app.screen
        assert isinstance(setup, SetupScreen)
        setup.action_select_manual()
        setup.action_start_game()
        await pilot.pause()
        game = app.game_screen
        assert game is not None
        if game._animation_timer is not None:
            game._animation_timer.pause()
        game.animation_controller.cancel()
        for _ in range(10):
            game.animation_controller.enqueue(build_intro_events())
        before = len(game.query("*"))
        for _ in range(50):
            game.animation_controller.advance()
            game.refresh_game_frame()
        assert len(game.query("*")) == before

    run_scenario(scenario)


def test_building_visual_events_does_not_change_the_seeded_outcome() -> None:
    async def scenario(pilot: Any, app: RetroGameApp) -> None:
        setup = app.screen
        assert isinstance(setup, SetupScreen)
        setup.action_select_autonomous()
        setup.action_start_game()
        await pilot.pause()
        game = app.game_screen
        assert game is not None
        game.animation_controller.cancel()
        while not game.session.engine.is_over:
            assert game.advance_one_turn()
            game.animation_controller.cancel()
        game.advance_one_turn()

        world, agent = main.build_game(42)
        assert game.outcome == GameEngine(world, agent).run()

    run_scenario(scenario)


def test_debug_view_is_observation_only_for_the_same_manual_actions() -> None:
    actions = (Action.TURN_RIGHT, Action.MOVE_FORWARD, Action.TURN_LEFT, Action.GRAB)
    quiet = main.build_session(SessionSettings(GameMode.MANUAL, 42))
    debugged = main.build_session(SessionSettings(GameMode.MANUAL, 42))
    assert quiet.manual_action_submitter is not None
    assert debugged.manual_action_submitter is not None
    assert debugged.debug_map_source is not None

    for action in actions:
        quiet.manual_action_submitter(action)
        quiet_result = quiet.engine.step()
        debugged.debug_map_source()
        debugged.manual_action_submitter(action)
        debug_result = debugged.engine.step()
        assert debug_result == quiet_result
