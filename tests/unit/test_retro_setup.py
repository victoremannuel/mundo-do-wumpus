"""Textual setup, manual controls, and restart lifecycle."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from textual.widgets import Button, Input

import main
from wumpus.domain import Action
from wumpus.game import GameEngine
from wumpus.game import GameObjective
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
        assert app.screen.selected_objective is None
        assert app.screen.query_one("#start-game", Button).disabled
        assert [
            app.screen.query_one(f"#{field}", Input).value
            for field in ("wumpus-count", "pit-count", "gold-count", "bat-count")
        ] == ["2", "4", "3", "2"]

    run_scenario(scenario)


def test_setup_requires_an_explicit_objective_after_mode_selection() -> None:
    async def scenario(pilot: Any, app: RetroGameApp) -> None:
        assert isinstance(app.screen, SetupScreen)
        await pilot.press("1")
        assert app.screen.query_one("#start-game", Button).disabled
        await pilot.press("enter")
        assert isinstance(app.screen, SetupScreen)
        await pilot.press("3", "enter")
        await pilot.pause()
        assert isinstance(app.screen, GameScreen)
        assert app.game_screen is not None
        assert app.game_screen.session.mode is GameMode.AUTONOMOUS
        assert app.game_screen.session.settings.objective is GameObjective.ESCAPE_FAST

    run_scenario(scenario)


def test_setup_requires_an_explicit_mode_after_objective_selection() -> None:
    """Both choices are deliberate; neither one alone may start a match."""

    async def scenario(pilot: Any, app: RetroGameApp) -> None:
        assert isinstance(app.screen, SetupScreen)
        await pilot.press("4")
        assert app.screen.selected_objective is GameObjective.COLLECT_ALL_GOLD
        assert app.screen.selected_mode is None
        assert app.screen.query_one("#start-game", Button).disabled
        await pilot.press("enter")
        assert isinstance(app.screen, SetupScreen)

        await pilot.press("2", "enter")
        await pilot.pause()
        assert isinstance(app.screen, GameScreen)
        assert app.game_screen is not None
        assert app.game_screen.session.mode is GameMode.MANUAL
        settings = app.game_screen.session.settings
        assert settings.objective is GameObjective.COLLECT_ALL_GOLD
        captured.append(settings)

    captured: list[SessionSettings] = []
    run_scenario(scenario)

    # The session hides the World from the interface, so prove the objective
    # reaches the environment at the factory seam the screen actually used.
    settings = captured[0]
    world, _agent = main.build_game(
        settings.seed, settings.config, objective=settings.objective
    )
    assert world.objective is GameObjective.COLLECT_ALL_GOLD


@pytest.mark.parametrize(
    ("objective_key", "objective", "label"),
    (
        ("3", GameObjective.ESCAPE_FAST, "ESCAPAR RÁPIDO"),
        ("4", GameObjective.COLLECT_ALL_GOLD, "TODOS OS OUROS"),
    ),
)
def test_the_hud_names_the_objective_and_the_exit_room(
    objective_key: str, objective: GameObjective, label: str
) -> None:
    async def scenario(pilot: Any, app: RetroGameApp) -> None:
        await pilot.press("1", objective_key, "enter")
        await pilot.pause()
        assert app.game_screen is not None
        assert app.game_screen.session.settings.objective is objective

        hud = app.screen.query_one("#status").visual.plain
        assert "OBJETIVO" in hud
        assert label in hud
        assert "SAÍDA" in hud
        assert "[1,1]" in hud

    run_scenario(scenario)


def test_the_final_summary_reports_the_objective_and_both_structural_rooms() -> None:
    async def scenario(pilot: Any, app: RetroGameApp) -> None:
        await pilot.press("1", "3", "enter")
        await pilot.pause()
        screen = app.game_screen
        assert screen is not None
        while not screen.session.engine.is_over:
            await pilot.press("n")
        await pilot.pause(1.0)

        summary = app.screen.query_one("#endgame").visual.plain
        for label in (
            "MODO", "OBJETIVO", "RESULT", "SCORE", "GOLD", "WUMPUS",
            "TURNS", "VISITED", "SEED", "INÍCIO", "SAÍDA",
        ):
            assert label in summary, label
        assert "ESCAPAR RÁPIDO" in summary
        assert "[1,1]" in summary
        assert "[6,6]" in summary

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
        setup.action_select_escape_fast()
        setup.query_one("#wumpus-count", Input).value = "34"
        setup.query_one("#pit-count", Input).value = "0"
        setup.query_one("#gold-count", Input).value = "0"
        setup.query_one("#bat-count", Input).value = "0"
        setup.action_start_game()
        assert isinstance(app.screen, SetupScreen)
        error = setup.query_one("#setup-error").visual.plain
        assert "CONFIGURAÇÃO INVÁLIDA" in error
        assert "31 células" in error

    run_scenario(scenario)


def test_valid_selection_reaches_the_requested_session_and_custom_counts() -> None:
    async def scenario(pilot: Any, app: RetroGameApp) -> None:
        setup = app.screen
        assert isinstance(setup, SetupScreen)
        setup.action_select_autonomous()
        setup.action_select_collect_all_gold()
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
        setup.action_select_escape_fast()
        setup.action_start_game()
        await pilot.pause(1.0)
        assert app.game_screen is not None
        assert app.game_screen.session.engine.turns == 0
        assert app.game_screen.state_label == "JOGADOR"

    run_scenario(scenario)


@pytest.mark.parametrize(
    ("key", "action"),
    (("up", Action.MOVE_FORWARD), ("left", Action.TURN_RIGHT),
     ("right", Action.TURN_RIGHT), ("g", Action.GRAB),
     ("f", Action.SHOOT)),
)
def test_each_manual_key_executes_exactly_one_engine_turn(key: str, action: Action) -> None:
    async def scenario(pilot: Any, app: RetroGameApp) -> None:
        setup = app.screen
        assert isinstance(setup, SetupScreen)
        setup.action_select_manual()
        setup.action_select_escape_fast()
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
        setup.action_select_escape_fast()
        setup.action_start_game()
        await pilot.pause(1.0)
        game = app.game_screen
        assert game is not None
        # Isolate the action animation under test from the independently
        # scheduled introductory animation, whose wall-clock completion can
        # vary under a full suite load.
        game.animation_controller.cancel()
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
        setup.action_select_collect_all_gold()
        setup.action_start_game()
        await pilot.pause()
        old_game = app.game_screen
        assert old_game is not None
        old_engine = old_game.session.engine
        assert old_game.animation_controller.busy

        await pilot.press("r")
        assert isinstance(app.screen, SetupScreen)
        assert app.screen.selected_mode is GameMode.AUTONOMOUS
        assert app.screen.selected_objective is GameObjective.COLLECT_ALL_GOLD
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


def test_automatic_seed_is_shown_and_restart_uses_the_next_map() -> None:
    app = RetroGameApp(
        session_factory=main.build_session,
        seed=None,
        start_paused=True,
    )

    async def runner() -> None:
        async with app.run_test(size=(MIN_WIDTH, MIN_HEIGHT)) as pilot:
            await pilot.press("2", "4", "enter")
            await pilot.pause()
            first = app.game_screen
            assert first is not None
            seed = first.session.settings.seed
            assert isinstance(seed, int)
            hud = app.screen.query_one("#status").visual.plain
            assert "SEED" in hud and str(seed) in hud
            assert first.session.debug_map_source is not None
            tiles = first.session.debug_map_source().tiles

            await pilot.press("r")
            app.screen.action_start_game()
            await pilot.pause()
            second = app.game_screen
            assert second is not None
            assert second.session.settings.seed == seed
            assert second.session.debug_map_source is not None
            assert second.session.settings.restart_index == 1
            assert second.session.debug_map_source().tiles != tiles

    asyncio.run(runner())


def test_restart_also_works_after_game_over() -> None:
    async def scenario(pilot: Any, app: RetroGameApp) -> None:
        setup = app.screen
        assert isinstance(setup, SetupScreen)
        setup.action_select_manual()
        setup.action_select_escape_fast()
        setup.action_start_game()
        await pilot.pause(1.0)
        game = app.game_screen
        assert game is not None
        game.animation_controller.cancel()
        for action in (
            (Action.MOVE_FORWARD,) * 5
            + (Action.TURN_RIGHT,)
            + (Action.MOVE_FORWARD,) * 5
            + (Action.CLIMB,)
        ):
            game._manual_action(action)
            game.animation_controller.cancel()
        game.advance_one_turn()
        assert game.finished
        await pilot.press("r")
        assert isinstance(app.screen, SetupScreen)

    run_scenario(scenario)


def test_fifty_animation_frames_keep_the_widget_tree_stable() -> None:
    async def scenario(pilot: Any, app: RetroGameApp) -> None:
        setup = app.screen
        assert isinstance(setup, SetupScreen)
        setup.action_select_manual()
        setup.action_select_escape_fast()
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
        setup.action_select_escape_fast()
        setup.action_start_game()
        await pilot.pause()
        game = app.game_screen
        assert game is not None
        game.animation_controller.cancel()
        while not game.session.engine.is_over:
            assert game.advance_one_turn()
            game.animation_controller.cancel()
        game.advance_one_turn()

        world, agent = main.build_game(42, objective=GameObjective.ESCAPE_FAST)
        assert game.outcome == GameEngine(world, agent).run()

    run_scenario(scenario)


def test_debug_view_is_observation_only_for_the_same_manual_actions() -> None:
    actions = (Action.TURN_RIGHT, Action.MOVE_FORWARD, Action.TURN_RIGHT, Action.GRAB)
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
