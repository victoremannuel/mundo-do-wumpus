import random
from collections.abc import Mapping, Sequence

import pytest

from wumpus.agent import SimpleAgent
from wumpus.domain import (
    Action,
    ActionResult,
    AgentObservation,
    Direction,
    EntityType,
    Position,
)
from wumpus.environment import GeneratedMap, World
from wumpus.game import GameEngine, GameOutcome, GameStatus, MAX_TURNS


class ScriptedAgent:
    """Agent that replays a fixed action script and records observations."""

    def __init__(self, actions: Sequence[Action], *, fallback: Action) -> None:
        self._actions = list(actions)
        self._fallback = fallback
        self.observations: list[AgentObservation] = []
        self.results: list[ActionResult] = []

    def decide(self, observation: AgentObservation) -> Action:
        self.observations.append(observation)
        if self._actions:
            return self._actions.pop(0)
        return self._fallback

    def process_result(self, result: ActionResult) -> None:
        self.results.append(result)


def world_with(
    entities: Mapping[Position, EntityType] | None = None,
) -> World:
    return World(
        GeneratedMap(rows=6, cols=6, entities=entities or {}),
        rng=random.Random(0),
    )


# Navigate the default 6x6 map from [1,1] to the far-corner exit [6,6],
# then climb: five moves north, turn east, five moves east, climb.
EXIT_SCRIPT = (
    (Action.MOVE_FORWARD,) * 5
    + (Action.TURN_RIGHT,)
    + (Action.MOVE_FORWARD,) * 5
    + (Action.CLIMB,)
)


def test_engine_stops_when_the_agent_climbs_at_the_exit() -> None:
    world = world_with()
    agent = ScriptedAgent(EXIT_SCRIPT, fallback=Action.TURN_RIGHT)
    engine = GameEngine(world, agent)

    outcome = engine.run()

    assert outcome.status is GameStatus.ESCAPED
    assert outcome.escaped is True
    assert outcome.turns == len(EXIT_SCRIPT)
    assert engine.is_over is True


def test_engine_stops_when_the_agent_dies() -> None:
    world = world_with({Position(2, 1): EntityType.PIT})
    agent = ScriptedAgent([Action.MOVE_FORWARD], fallback=Action.MOVE_FORWARD)
    engine = GameEngine(world, agent)

    outcome = engine.run()

    assert outcome.status is GameStatus.DEAD
    assert outcome.escaped is False
    assert outcome.turns == 1
    assert world.dead is True


def test_engine_stops_at_the_technical_turn_limit() -> None:
    world = world_with()
    agent = ScriptedAgent([], fallback=Action.TURN_RIGHT)
    engine = GameEngine(world, agent, max_turns=7)

    outcome = engine.run()

    assert outcome.status is GameStatus.TURN_LIMIT
    assert outcome.turns == 7
    assert world.game_over is False


def test_default_turn_limit_matches_the_plan() -> None:
    assert MAX_TURNS == 2000
    engine = GameEngine(world_with(), ScriptedAgent([], fallback=Action.CLIMB))

    assert engine.max_turns == MAX_TURNS


def test_engine_rejects_a_non_positive_turn_limit() -> None:
    with pytest.raises(ValueError):
        GameEngine(world_with(), ScriptedAgent([], fallback=Action.CLIMB), max_turns=0)


def test_step_raises_after_the_game_is_over() -> None:
    world = world_with()
    engine = GameEngine(world, ScriptedAgent(EXIT_SCRIPT, fallback=Action.TURN_RIGHT))

    engine.run()

    with pytest.raises(RuntimeError):
        engine.step()


def test_engine_follows_the_perceive_decide_act_learn_cycle() -> None:
    world = world_with({Position(1, 1): EntityType.GOLD})
    agent = ScriptedAgent([Action.GRAB, *EXIT_SCRIPT], fallback=Action.TURN_RIGHT)
    engine = GameEngine(world, agent)

    outcome = engine.run()

    assert [observation.position for observation in agent.observations[:2]] == [Position(1, 1), Position(1, 1)]
    assert agent.observations[0].collected_gold == 0
    assert agent.observations[0].perception.glitter is True
    assert agent.observations[1].collected_gold == 1
    assert [result.action for result in agent.results[:2]] == [Action.GRAB, Action.MOVE_FORWARD]
    assert outcome.collected_gold == 1
    assert outcome.score == world.score


def test_engine_reports_visited_cells_and_killed_wumpus() -> None:
    world = world_with({Position(3, 1): EntityType.WUMPUS})
    agent = ScriptedAgent(
        [Action.SHOOT, Action.MOVE_FORWARD, Action.MOVE_FORWARD],
        fallback=Action.CLIMB,
    )
    engine = GameEngine(world, agent, max_turns=3)

    outcome = engine.run()

    assert outcome.killed_wumpus == 1
    assert outcome.visited_cells == 3
    assert engine.visited_cells == frozenset(
        {Position(1, 1), Position(2, 1), Position(3, 1)}
    )


def test_engine_renders_before_deciding_and_renders_final_after_learning() -> None:
    events: list[str] = []

    class RecordingWorld(World):
        def observation(self) -> AgentObservation:
            events.append("observe")
            return super().observation()

        def execute(self, action: Action) -> ActionResult:
            events.append("execute")
            return super().execute(action)

    class RecordingAgent(ScriptedAgent):
        def decide(self, observation: AgentObservation) -> Action:
            events.append("decide")
            return super().decide(observation)

        def process_result(self, result: ActionResult) -> None:
            events.append("process_result")
            super().process_result(result)

    world = RecordingWorld(
        GeneratedMap(rows=2, cols=2, entities={}),
        rng=random.Random(0),
    )
    agent = RecordingAgent(
        # On a 2x2 map the exit is the far corner [2,2]: move north, turn
        # east, move east, then climb.
        [
            Action.MOVE_FORWARD,
            Action.TURN_RIGHT,
            Action.MOVE_FORWARD,
            Action.CLIMB,
        ],
        fallback=Action.TURN_RIGHT,
    )
    seen_observations: list[AgentObservation] = []
    seen_outcomes: list[GameOutcome] = []

    def render(observation: AgentObservation) -> None:
        events.append("render")
        seen_observations.append(observation)

    def render_final(outcome: GameOutcome) -> None:
        events.append("render_final")
        seen_outcomes.append(outcome)

    engine = GameEngine(
        world,
        agent,
        on_render=render,
        on_render_final=render_final,
    )

    outcome = engine.run()

    assert events == ["observe", "render", "decide", "execute", "process_result"] * 4 + ["render_final"]
    assert seen_observations == agent.observations
    assert seen_outcomes == [outcome]


@pytest.mark.parametrize(
    ("entities", "actions", "max_turns", "expected_status"),
    [
        ({}, EXIT_SCRIPT, 12, GameStatus.ESCAPED),
        ({Position(2, 1): EntityType.PIT}, (Action.MOVE_FORWARD,), 2, GameStatus.DEAD),
        ({}, (Action.TURN_RIGHT,), 1, GameStatus.TURN_LIMIT),
    ],
)
def test_engine_renders_final_for_every_terminal_status(
    entities: Mapping[Position, EntityType],
    actions: Sequence[Action],
    max_turns: int,
    expected_status: GameStatus,
) -> None:
    rendered: list[GameOutcome] = []
    engine = GameEngine(
        world_with(entities),
        ScriptedAgent(actions, fallback=actions[-1]),
        max_turns=max_turns,
        on_render_final=rendered.append,
    )

    outcome = engine.run()

    assert outcome.status is expected_status
    assert rendered == [outcome]


def test_outcome_is_unavailable_before_the_game_ends() -> None:
    world = world_with()
    engine = GameEngine(world, ScriptedAgent([], fallback=Action.TURN_RIGHT), max_turns=5)

    engine.step()
    with pytest.raises(RuntimeError, match="before the game is over"):
        engine.outcome()

    assert engine.turns == 1
    assert engine.is_over is False


def test_agent_only_receives_the_reduced_observation() -> None:
    world = world_with({Position(2, 1): EntityType.WUMPUS})
    agent = ScriptedAgent([Action.TURN_RIGHT], fallback=Action.CLIMB)
    engine = GameEngine(world, agent, max_turns=1)

    engine.run()
    observation = agent.observations[0]

    assert set(vars(observation)) == {
        "position",
        "direction",
        "perception",
        "score",
        "collected_gold",
        "active",
    }
    assert observation.direction is Direction.NORTH
    assert observation.active is True
    assert not any(isinstance(value, World) for value in vars(observation).values())


def test_observation_reports_an_inactive_agent_after_the_game_ends() -> None:
    world = world_with()
    for action in EXIT_SCRIPT:
        world.execute(action)

    observation = world.observation()

    assert observation.active is False
    assert observation.position == Position(6, 6)


def test_seeded_games_with_the_simple_agent_are_reproducible() -> None:
    def play(seed: int) -> GameOutcome:
        world = World(
            GeneratedMap(
                rows=6,
                cols=6,
                entities={
                    Position(4, 4): EntityType.PIT,
                    Position(2, 4): EntityType.GOLD,
                    Position(5, 2): EntityType.WUMPUS,
                },
            ),
            rng=random.Random(seed),
        )
        engine = GameEngine(world, SimpleAgent(random.Random(seed)), max_turns=200)
        return engine.run()

    first = play(2026)
    second = play(2026)

    assert first == second
    assert first.turns <= 200
