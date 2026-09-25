"""End-to-end deterministic runs over procedurally generated worlds."""

import pytest

from main import build_game
from wumpus.game import MAX_TURNS, GameEngine, GameOutcome, GameStatus


FIXED_SEEDS = (1, 2, 3, 10, 20, 42, 100, 123, 999, 2026)


def play(seed: int) -> GameOutcome:
    """Run the production composition without console delays or rendering."""

    world, agent = build_game(seed)
    engine = GameEngine(world, agent)
    outcome = engine.run()

    assert engine.is_over
    assert 1 <= outcome.turns <= MAX_TURNS
    assert outcome.status in {
        GameStatus.ESCAPED,
        GameStatus.DEAD,
        GameStatus.TURN_LIMIT,
    }
    return outcome


@pytest.mark.parametrize("seed", FIXED_SEEDS)
def test_generated_games_terminate_reproducibly_without_exceptions(seed: int) -> None:
    first = play(seed)
    replay = play(seed)

    assert replay == first
