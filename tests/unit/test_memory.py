import random

from wumpus.agent import AgentMemory, KnowledgeBase, SimpleAgent
from wumpus.domain import (
    Action,
    ActionResult,
    AgentObservation,
    Direction,
    EntityType,
    Perception,
    Position,
)
from wumpus.environment import GeneratedMap, World
from wumpus.game import GameEngine, GameStatus


NO_PERCEPTION = Perception(
    stench=False,
    breeze=False,
    bat_noise=False,
    glitter=False,
    bump=False,
    scream=False,
)


def new_memory() -> AgentMemory:
    return AgentMemory(
        Position(1, 1),
        Direction.NORTH,
        KnowledgeBase(rows=6, cols=6),
    )


def observation(
    position: Position,
    *,
    direction: Direction = Direction.NORTH,
    perception: Perception = NO_PERCEPTION,
    score: int = 0,
    collected_gold: int = 0,
) -> AgentObservation:
    return AgentObservation(
        position=position,
        direction=direction,
        perception=perception,
        score=score,
        collected_gold=collected_gold,
        active=True,
    )


def action_result(
    action: Action,
    position: Position,
    *,
    direction: Direction = Direction.NORTH,
    perception: Perception = NO_PERCEPTION,
    score_delta: int = -1,
    total_score: int = -1,
    gold_collected: bool = False,
) -> ActionResult:
    return ActionResult(
        action=action,
        position=position,
        direction=direction,
        score_delta=score_delta,
        total_score=total_score,
        perception=perception,
        gold_collected=gold_collected,
    )


def test_memory_starts_with_only_the_known_initial_state() -> None:
    memory = new_memory()

    assert memory.position == Position(1, 1)
    assert memory.direction is Direction.NORTH
    assert memory.visited == frozenset({Position(1, 1)})
    assert memory.path == (Position(1, 1),)
    assert memory.perception_history == ()
    assert memory.actions == ()
    assert memory.score == 0
    assert memory.collected_gold == 0


def test_memory_records_observations_without_inferring_hazards() -> None:
    memory = new_memory()
    sensed = Perception(
        stench=True,
        breeze=True,
        bat_noise=False,
        glitter=True,
        bump=False,
        scream=False,
    )

    memory.record_observation(
        observation(
            Position(2, 1),
            direction=Direction.EAST,
            perception=sensed,
            score=-4,
        )
    )

    record = memory.perception_history[-1]
    assert memory.position == Position(2, 1)
    assert memory.direction is Direction.EAST
    assert memory.visited == frozenset({Position(1, 1), Position(2, 1)})
    assert memory.gold_seen == frozenset({Position(2, 1)})
    assert memory.score == -4
    assert record.perception is sensed
    assert record.action is None
    assert not hasattr(memory, "possible_pits")
    assert not hasattr(memory, "confirmed_wumpus")


def test_memory_records_executed_actions_results_and_travel_path() -> None:
    memory = new_memory()

    memory.record_result(
        action_result(Action.MOVE_FORWARD, Position(2, 1), total_score=-1)
    )
    memory.record_result(
        action_result(
            Action.TURN_RIGHT,
            Position(2, 1),
            direction=Direction.EAST,
            total_score=-2,
        )
    )

    assert memory.position == Position(2, 1)
    assert memory.direction is Direction.EAST
    assert memory.visited == frozenset({Position(1, 1), Position(2, 1)})
    assert memory.path == (Position(1, 1), Position(2, 1))
    assert memory.actions == (Action.MOVE_FORWARD, Action.TURN_RIGHT)
    assert memory.score == -2
    assert [record.action for record in memory.perception_history] == [
        Action.MOVE_FORWARD,
        Action.TURN_RIGHT,
    ]


def test_memory_preserves_repeated_perceptions_in_chronological_order() -> None:
    memory = new_memory()
    breeze = Perception(**{**vars(NO_PERCEPTION), "breeze": True})

    memory.record_observation(observation(Position(1, 1), perception=breeze))
    memory.record_observation(observation(Position(1, 1)))

    assert [record.perception for record in memory.perception_history] == [
        breeze,
        NO_PERCEPTION,
    ]


def test_memory_preserves_transient_perceptions_from_action_results() -> None:
    memory = new_memory()
    transient = Perception(
        stench=False,
        breeze=False,
        bat_noise=False,
        glitter=False,
        bump=True,
        scream=True,
    )

    memory.record_result(
        action_result(
            Action.SHOOT,
            Position(1, 1),
            perception=transient,
            score_delta=-10,
            total_score=-10,
        )
    )

    record = memory.perception_history[-1]
    assert record.action is Action.SHOOT
    assert record.perception.bump is True
    assert record.perception.scream is True


def test_memory_updates_gold_count_immediately_after_a_successful_grab() -> None:
    memory = new_memory()

    memory.record_result(
        action_result(
            Action.GRAB,
            Position(1, 1),
            score_delta=999,
            total_score=999,
            gold_collected=True,
        )
    )

    assert memory.collected_gold == 1
    assert memory.actions == (Action.GRAB,)
    assert memory.score == 999


def test_simple_agent_memory_is_updated_by_the_real_game_loop() -> None:
    world = World(
        GeneratedMap(
            rows=6,
            cols=6,
            entities={Position(1, 1): EntityType.GOLD},
        ),
        rng=random.Random(0),
    )
    agent = SimpleAgent(random.Random(0))

    outcome = GameEngine(world, agent).run()

    assert outcome.status is GameStatus.ESCAPED
    assert agent.memory.visited == frozenset({Position(1, 1)})
    assert agent.memory.path == (Position(1, 1),)
    assert agent.memory.actions == (Action.GRAB, Action.CLIMB)
    assert agent.memory.collected_gold == 1
    assert agent.memory.score == 998
    assert agent.memory.gold_seen == frozenset({Position(1, 1)})


def test_simple_agent_inference_updates_knowledge_from_reduced_observations() -> None:
    agent = SimpleAgent(random.Random(0))

    agent.decide(observation(Position(1, 1)))

    neighbors = frozenset({Position(1, 2), Position(2, 1)})
    assert neighbors.issubset(agent.memory.knowledge.safe)
    assert neighbors.issubset(agent.memory.knowledge.not_pit)
    assert neighbors.issubset(agent.memory.knowledge.not_wumpus)
    assert neighbors.issubset(agent.memory.knowledge.not_bat)
