"""Generated-map solvability and deterministic restart-sequence regressions."""

import random
from collections import Counter, deque

import main
from wumpus.domain import EntityType, Position
from wumpus.environment import MapGenerator, is_world_solvable
from wumpus.game import GameConfig
from wumpus.ui.retro_session import GameMode, SessionSettings


def reachable(generated) -> set[Position]:
    pending = deque([Position(1, 1)])
    seen = set(pending)
    blockers = {EntityType.PIT, EntityType.WUMPUS, EntityType.BAT}
    while pending:
        position = pending.popleft()
        for candidate in position.neighbors():
            if (
                candidate.is_inside(generated.rows, generated.cols)
                and candidate not in seen
                and generated.entity_at(candidate) not in blockers
            ):
                seen.add(candidate)
                pending.append(candidate)
    return seen


def signature(session) -> tuple[tuple[Position, object], ...]:
    assert session.debug_map_source is not None
    return tuple(sorted(session.debug_map_source().tiles.items()))


def test_one_hundred_seeded_maps_keep_invariants_and_a_safe_gold_return_route() -> None:
    config = GameConfig()
    expected = {
        EntityType.WUMPUS: 2,
        EntityType.PIT: 4,
        EntityType.GOLD: 3,
        EntityType.BAT: 2,
    }
    for seed in range(100):
        generated = MapGenerator(random.Random(seed), config).generate()
        accessible = reachable(generated)
        assert (generated.rows, generated.cols) == (6, 6)
        assert Counter(generated.entities.values()) == expected
        assert len(generated.entities) == len(set(generated.entities)) == 11
        assert all(cell not in generated.entities for cell in (Position(1, 1), Position(1, 2), Position(2, 1)))
        assert is_world_solvable(generated)
        assert any(
            entity is EntityType.GOLD and position in accessible
            for position, entity in generated.entities.items()
        )
        assert Position(1, 1) in accessible  # BFS component makes return possible.


def test_twenty_restarts_never_repeat_the_immediately_previous_layout() -> None:
    settings = SessionSettings(GameMode.MANUAL, seed=42, game_config=GameConfig())
    signatures = []
    for _ in range(20):
        session = main.build_session(settings)
        signatures.append(signature(session))
        assert session.next_settings is not None
        settings = session.next_settings

    assert all(first != second for first, second in zip(signatures, signatures[1:]))


def test_same_base_seed_replays_the_same_variable_restart_sequence() -> None:
    def sequence() -> list[tuple[tuple[Position, object], ...]]:
        settings = SessionSettings(GameMode.MANUAL, seed=42, game_config=GameConfig())
        maps = []
        for _ in range(3):
            session = main.build_session(settings)
            maps.append(signature(session))
            assert session.next_settings is not None
            settings = session.next_settings
        return maps

    first = sequence()
    second = sequence()
    assert first == second
    assert first[0] != first[1]
    assert first[1] != first[2]
