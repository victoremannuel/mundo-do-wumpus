"""Tests for the command-line entry point (`main.py`).

`run()` stays the headless, legacy-console path these tests exercise; the retro
interface has its own tests in `test_retro_app.py` and is never started here.
"""

from __future__ import annotations

import builtins
import time

import pytest

import main
from wumpus.game import GameStatus


def test_parse_args_defaults() -> None:
    args = main.parse_args([])

    assert args.seed is None
    assert args.debug is False
    assert args.step is False
    assert args.delay == main.DEFAULT_DELAY
    assert args.no_delay is False
    assert args.legacy_console is False


def test_parse_args_all_flags() -> None:
    args = main.parse_args(
        [
            "--seed",
            "42",
            "--debug",
            "--step",
            "--delay",
            "1.5",
            "--no-delay",
            "--legacy-console",
        ]
    )

    assert args.seed == 42
    assert args.debug is True
    assert args.step is True
    assert args.delay == 1.5
    assert args.no_delay is True
    assert args.legacy_console is True


def test_build_game_is_deterministic_for_the_same_seed() -> None:
    world_a, agent_a = main.build_game(42)
    world_b, agent_b = main.build_game(42)

    from wumpus.game import GameEngine

    outcome_a = GameEngine(world_a, agent_a, max_turns=500).run()
    outcome_b = GameEngine(world_b, agent_b, max_turns=500).run()

    assert outcome_a.status == outcome_b.status
    assert outcome_a.score == outcome_b.score
    assert outcome_a.turns == outcome_b.turns


def test_run_with_no_delay_never_sleeps_and_reaches_a_terminal_status(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail_sleep(_seconds: float) -> None:
        raise AssertionError("time.sleep must not be called with --no-delay")

    monkeypatch.setattr(time, "sleep", fail_sleep)

    outcome = main.run(["--seed", "20", "--no-delay"])
    output = capsys.readouterr().out

    assert outcome.status in (
        GameStatus.ESCAPED,
        GameStatus.DEAD,
        GameStatus.TURN_LIMIT,
        GameStatus.ABANDONED,
    )
    if outcome.status is GameStatus.ESCAPED:
        assert "ESCAPOU DA CAVERNA" in output
    elif outcome.status is GameStatus.DEAD:
        assert "AGENTE MORREU" in output


def test_run_with_step_prompts_for_enter_once_per_turn(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    prompts: list[str] = []

    def fake_input(prompt: str = "") -> str:
        prompts.append(prompt)
        return ""

    def fail_sleep(_seconds: float) -> None:
        raise AssertionError("time.sleep must not be called in --step mode")

    monkeypatch.setattr(builtins, "input", fake_input)
    monkeypatch.setattr(time, "sleep", fail_sleep)

    outcome = main.run(["--seed", "20", "--step"])

    assert len(prompts) == outcome.turns


def test_run_with_debug_renders_the_real_map(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)

    main.run(["--seed", "20", "--debug", "--delay", "0"])
    output = capsys.readouterr().out

    assert "MAPA REAL" in output


def test_run_without_debug_never_renders_the_real_map(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)

    main.run(["--seed", "20", "--delay", "0"])
    output = capsys.readouterr().out

    assert "MAPA REAL" not in output


def test_legacy_console_dispatches_to_the_headless_renderer(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail_tui(_args: object) -> None:
        raise AssertionError("--legacy-console must never start the retro interface")

    monkeypatch.setattr(main, "run_tui", fail_tui)

    outcome = main.main(["--seed", "20", "--no-delay", "--legacy-console"])
    output = capsys.readouterr().out

    assert outcome is not None
    assert outcome.status in (
        GameStatus.ESCAPED,
        GameStatus.DEAD,
        GameStatus.TURN_LIMIT,
        GameStatus.ABANDONED,
    )
    assert "MAPA CONHECIDO PELO AGENTE" in output


def test_the_retro_interface_is_the_default_front_end(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launched: list[object] = []

    def fake_tui(args: object) -> None:
        launched.append(args)
        return None

    def fail_run(_argv: object) -> None:
        raise AssertionError("the default front end must not be the legacy console")

    monkeypatch.setattr(main, "run_tui", fake_tui)
    monkeypatch.setattr(main, "run", fail_run)

    assert main.main(["--seed", "7"]) is None
    assert len(launched) == 1


def test_speed_index_never_selects_a_zero_interval() -> None:
    from wumpus.ui.retro_state import MAX_SPEED_INDEX, SPEED_INTERVALS

    assert main.speed_index_for(main.DEFAULT_DELAY, no_delay=False) == (
        SPEED_INTERVALS.index(main.DEFAULT_DELAY)
    )
    assert main.speed_index_for(0.0, no_delay=True) == MAX_SPEED_INDEX
    for delay in (0.0, 0.01, 0.5, 3.0):
        index = main.speed_index_for(delay, no_delay=False)
        assert 0 <= index <= MAX_SPEED_INDEX
        assert SPEED_INTERVALS[index] > 0
