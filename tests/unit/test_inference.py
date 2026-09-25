import pytest

from wumpus.agent import (
    MAX_INFERENCE_CYCLES,
    InferenceConflictError,
    InferenceEngine,
    InferenceLimitError,
    KnowledgeBase,
)
from wumpus.domain import EntityType, Perception, Position


def perception(
    *,
    breeze: bool = False,
    stench: bool = False,
    bat_noise: bool = False,
) -> Perception:
    return Perception(
        stench=stench,
        breeze=breeze,
        bat_noise=bat_noise,
        glitter=False,
        bump=False,
        scream=False,
    )


def test_absent_signals_create_negative_knowledge_and_safe_neighbors() -> None:
    base = KnowledgeBase(6, 6)
    engine = InferenceEngine(base)

    engine.observe(Position(1, 1), perception())

    neighbors = frozenset({Position(1, 2), Position(2, 1)})
    assert neighbors.issubset(base.not_pit)
    assert neighbors.issubset(base.not_wumpus)
    assert neighbors.issubset(base.not_bat)
    assert neighbors.issubset(base.safe)


@pytest.mark.parametrize(
    ("hazard", "signal", "attribute"),
    [
        (EntityType.PIT, {"breeze": True}, "possible_pits"),
        (EntityType.WUMPUS, {"stench": True}, "possible_wumpus"),
        (EntityType.BAT, {"bat_noise": True}, "possible_bats"),
    ],
)
def test_present_signals_add_typed_candidates(
    hazard: EntityType,
    signal: dict[str, bool],
    attribute: str,
) -> None:
    base = KnowledgeBase(6, 6)
    engine = InferenceEngine(base)

    engine.observe(Position(1, 1), perception(**signal))

    assert getattr(base, attribute) == frozenset(
        {Position(1, 2), Position(2, 1)}
    )
    assert hazard in (EntityType.PIT, EntityType.WUMPUS, EntityType.BAT)


def test_elimination_confirms_the_only_remaining_candidate() -> None:
    base = KnowledgeBase(6, 6)
    base.mark_not(Position(1, 2), EntityType.PIT)
    engine = InferenceEngine(base)

    engine.observe(Position(1, 1), perception(breeze=True))

    assert base.confirmed_pits == frozenset({Position(2, 1)})


@pytest.mark.parametrize(
    ("hazard", "signal"),
    [
        (EntityType.PIT, {"breeze": True}),
        (EntityType.WUMPUS, {"stench": True}),
        (EntityType.BAT, {"bat_noise": True}),
    ],
)
def test_positive_signal_with_no_candidate_fails_closed(
    hazard: EntityType,
    signal: dict[str, bool],
) -> None:
    base = KnowledgeBase(6, 6)
    base.mark_not(Position(1, 2), hazard)
    base.mark_not(Position(2, 1), hazard)
    engine = InferenceEngine(base)

    with pytest.raises(InferenceConflictError):
        engine.observe(Position(1, 1), perception(**signal))


def test_inference_runs_to_a_stable_idempotent_fixed_point() -> None:
    base = KnowledgeBase(6, 6)
    engine = InferenceEngine(base)
    observed = perception(breeze=True)

    engine.observe(Position(1, 1), observed)
    revision = base.revision
    events = engine.events
    engine.observe(Position(1, 1), observed)

    assert base.revision == revision
    assert engine.events == events


def test_inference_events_contain_only_functional_rule_evidence() -> None:
    base = KnowledgeBase(6, 6)
    engine = InferenceEngine(base)

    engine.observe(Position(1, 1), perception())

    assert engine.events
    assert all(event.rule for event in engine.events)
    assert all(event.source == Position(1, 1) for event in engine.events)
    assert all(event.affected for event in engine.events)


def test_inference_is_bounded_and_rejects_invalid_limits() -> None:
    with pytest.raises(ValueError):
        InferenceEngine(KnowledgeBase(6, 6), max_cycles=0)

    base = KnowledgeBase(6, 6)
    with pytest.raises(InferenceLimitError):
        InferenceEngine(base, max_cycles=1).observe(Position(1, 1), perception())

    assert MAX_INFERENCE_CYCLES == 100


def test_out_of_bounds_observations_are_rejected() -> None:
    engine = InferenceEngine(KnowledgeBase(6, 6))

    with pytest.raises(ValueError):
        engine.observe(Position(7, 1), perception())
