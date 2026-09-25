"""Tests for the FASE 18 command-line entry point (`main.py`)."""

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


def test_parse_args_all_flags() -> None:
    args = main.parse_args(
        ["--seed", "42", "--debug", "--step", "--delay", "1.5", "--no-delay"]
    )

    assert args.seed == 42
    assert args.debug is True
    assert args.step is True
    assert args.delay == 1.5
    assert args.no_delay is True


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

    outcome = main.run(["--seed", "7", "--no-delay"])
    output = capsys.readouterr().out

    assert outcome.status in (GameStatus.ESCAPED, GameStatus.DEAD, GameStatus.TURN_LIMIT)
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

    outcome = main.run(["--seed", "7", "--step"])

    assert len(prompts) == outcome.turns


def test_run_with_debug_renders_the_real_map(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)

    main.run(["--seed", "7", "--debug", "--delay", "0"])
    output = capsys.readouterr().out

    assert "MAPA REAL" in output


def test_run_without_debug_never_renders_the_real_map(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)

    main.run(["--seed", "7", "--delay", "0"])
    output = capsys.readouterr().out

    assert "MAPA REAL" not in output
