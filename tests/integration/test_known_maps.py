"""Integration tests for the real agent running against known maps."""

from __future__ import annotations

import random
from collections.abc import Mapping

from wumpus.agent import SimpleAgent
from wumpus.domain import Action, EntityType, Position
from wumpus.environment import GeneratedMap, World
from wumpus.game import GameConfig, GameEngine, GameOutcome, GameStatus


def run_known_map(
    *,
    config: GameConfig,
    entities: Mapping[Position, EntityType],
    seed: int = 19,
) -> tuple[World, SimpleAgent, GameOutcome]:
    """Run the production agent/environment/engine stack without test doubles."""

    rng = random.Random(seed)
    world = World(
        GeneratedMap(rows=config.rows, cols=config.cols, entities=entities),
        rng=rng,
    )
    agent = SimpleAgent(rng, config=config)
    outcome = GameEngine(world, agent, max_turns=300).run()
    return world, agent, outcome


def test_real_agent_collects_known_gold_and_returns_to_the_exit() -> None:
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
    assert world.agent_position == Position(1, 1)
    assert gold in agent.memory.visited
    assert Action.GRAB in agent.memory.actions
    assert agent.memory.actions[-1] is Action.CLIMB


def test_real_agent_infers_hazards_hunts_and_escapes_a_mixed_map() -> None:
    wumpus = Position(3, 1)
    pit = Position(2, 3)
    gold = Position(4, 4)
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
    assert world.agent_position == Position(1, 1)
    assert pit not in agent.memory.visited
    assert pit in agent.memory.knowledge.confirmed_pits
    assert wumpus in agent.memory.knowledge.dead_wumpus
    assert Action.SHOOT in agent.memory.actions
    assert Action.GRAB in agent.memory.actions
    assert agent.memory.actions[-1] is Action.CLIMB
