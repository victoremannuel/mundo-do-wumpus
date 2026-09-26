"""Integration tests for the real agent running against known maps."""

from __future__ import annotations

import random
from collections.abc import Mapping

from wumpus.agent import SimpleAgent
from wumpus.domain import Action, EntityType, Position
from wumpus.environment import GeneratedMap, World
from wumpus.game import GameConfig, GameEngine, GameObjective, GameOutcome, GameStatus


def run_known_map(
    *,
    config: GameConfig,
    entities: Mapping[Position, EntityType],
    seed: int = 19,
    objective: GameObjective = GameObjective.COLLECT_ALL_GOLD,
) -> tuple[World, SimpleAgent, GameOutcome]:
    """Run the production agent/environment/engine stack without test doubles."""

    rng = random.Random(seed)
    world = World(
        GeneratedMap(rows=config.rows, cols=config.cols, entities=entities),
        rng=rng,
        objective=objective,
    )
    agent = SimpleAgent(rng, config=config, objective=objective)
    outcome = GameEngine(world, agent, max_turns=300).run()
    return world, agent, outcome


def test_real_agent_collects_known_gold_and_climbs_at_the_exit() -> None:
    gold = Position(3, 1)
    config = GameConfig(
        rows=3,
        cols=3,
        wumpus_count=0,
        pit_count=0,
        gold_count=1,
        bat_count=0,
    )

    world, agent, outcome = run_known_map(
        config=config,
        entities={gold: EntityType.GOLD},
    )

    assert outcome.status is GameStatus.ESCAPED
    assert outcome.collected_gold == 1
    assert outcome.turns == agent.actions_taken
    assert outcome.score == world.score == agent.memory.score
    assert world.agent_position == config.exit_position
    assert gold in agent.memory.visited
    assert Action.GRAB in agent.memory.actions
    assert agent.memory.actions[-1] is Action.CLIMB


def test_real_agent_infers_hazards_hunts_and_escapes_a_mixed_map() -> None:
    wumpus = Position(3, 1)
    pit = Position(2, 3)
    gold = Position(4, 3)
    config = GameConfig(
        rows=4,
        cols=4,
        wumpus_count=1,
        pit_count=1,
        gold_count=1,
        bat_count=0,
    )

    world, agent, outcome = run_known_map(
        config=config,
        entities={
            wumpus: EntityType.WUMPUS,
            pit: EntityType.PIT,
            gold: EntityType.GOLD,
        },
    )

    assert outcome.status is GameStatus.ESCAPED
    assert outcome.collected_gold == 1
    assert outcome.killed_wumpus == 1
    assert outcome.turns == agent.actions_taken
    assert outcome.score == world.score == agent.memory.score
    assert world.agent_position == config.exit_position
    assert pit not in agent.memory.visited
    assert pit in agent.memory.knowledge.confirmed_pits
    assert wumpus in agent.memory.knowledge.dead_wumpus
    assert Action.SHOOT in agent.memory.actions
    assert Action.GRAB in agent.memory.actions
    assert agent.memory.actions[-1] is Action.CLIMB


def test_real_escape_fast_agent_grabs_incidental_gold_along_its_own_route() -> None:
    """FAST-ESCAPE-INCIDENTAL-GOLD-012 (DEC-012), proven on the real stack.

    ESCAPE_FAST never searches for gold and never detours toward it, but the
    gold here sits on the same straight-line room the agent naturally
    crosses on its way to the exit. `World` -> `AgentObservation` ->
    `Perception.glitter` -> `Strategy` must make the agent collect it instead
    of walking past it, without the test forcing any decision directly.
    """

    gold = Position(3, 1)
    config = GameConfig(
        rows=3,
        cols=3,
        wumpus_count=0,
        pit_count=0,
        gold_count=1,
        bat_count=0,
    )

    world, agent, outcome = run_known_map(
        config=config,
        entities={gold: EntityType.GOLD},
        objective=GameObjective.ESCAPE_FAST,
    )

    assert outcome.status is GameStatus.ESCAPED
    assert outcome.collected_gold == 1
    assert outcome.turns == agent.actions_taken
    assert outcome.score == world.score == agent.memory.score
    assert world.agent_position == config.exit_position
    assert gold in agent.memory.visited
    assert Action.GRAB in agent.memory.actions
    assert agent.memory.actions[-1] is Action.CLIMB
