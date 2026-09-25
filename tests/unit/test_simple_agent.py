import ast
import random
from pathlib import Path

from wumpus.agent import SimpleAgent
from wumpus.domain import (
    Action,
    ActionResult,
    AgentObservation,
    Direction,
    Perception,
    Position,
)


def perception(**overrides: bool) -> Perception:
    values = {
        "stench": False,
        "breeze": False,
        "bat_noise": False,
        "glitter": False,
        "bump": False,
        "scream": False,
    }
    values.update(overrides)
    return Perception(**values)


def observation(
    *,
    position: Position = Position(1, 1),
    collected_gold: int = 0,
    **perception_overrides: bool,
) -> AgentObservation:
    return AgentObservation(
        position=position,
        direction=Direction.NORTH,
        perception=perception(**perception_overrides),
        score=0,
        collected_gold=collected_gold,
        active=True,
    )


def result(action: Action, *, bump: bool = False) -> ActionResult:
    return ActionResult(
        action=action,
        position=Position(1, 1),
        direction=Direction.NORTH,
        score_delta=-1,
        total_score=-1,
        perception=perception(bump=bump),
    )


def test_agent_grabs_when_it_perceives_glitter() -> None:
    agent = SimpleAgent(random.Random(1))

    assert agent.decide(observation(glitter=True)) is Action.GRAB


def test_agent_climbs_at_the_start_with_gold_and_no_safe_frontier() -> None:
    # A clear scan at the start (no perceived danger) always reveals a safe,
    # unvisited neighbor, so climbing there requires evidence that keeps both
    # neighbors unresolved instead: a full house of positive signals.
    agent = SimpleAgent(random.Random(1))

    decision = agent.decide(
        observation(collected_gold=1, breeze=True, stench=True, bat_noise=True)
    )

    assert decision is Action.CLIMB


def test_agent_does_not_climb_carrying_gold_away_from_the_exit() -> None:
    agent = SimpleAgent(random.Random(1))

    decision = agent.decide(observation(position=Position(3, 2), collected_gold=1))

    assert decision is not Action.CLIMB


def test_agent_turns_after_a_bump() -> None:
    agent = SimpleAgent(random.Random(1))
    agent.process_result(result(Action.MOVE_FORWARD, bump=True))

    assert agent.decide(observation()) in (Action.TURN_LEFT, Action.TURN_RIGHT)


def test_agent_stops_turning_after_a_successful_move() -> None:
    agent = SimpleAgent(random.Random(1))
    agent.process_result(result(Action.MOVE_FORWARD, bump=True))
    agent.process_result(result(Action.MOVE_FORWARD))

    decisions = {agent.decide(observation()) for _ in range(50)}

    assert Action.MOVE_FORWARD in decisions


def test_agent_counts_processed_results() -> None:
    agent = SimpleAgent(random.Random(1))
    agent.process_result(result(Action.TURN_LEFT))
    agent.process_result(result(Action.TURN_LEFT))

    assert agent.actions_taken == 2


def test_agent_decisions_depend_only_on_the_injected_rng() -> None:
    first = SimpleAgent(random.Random(7))
    second = SimpleAgent(random.Random(7))

    assert [first.decide(observation()) for _ in range(30)] == [
        second.decide(observation()) for _ in range(30)
    ]


def test_agent_package_never_imports_the_environment_or_hidden_map_types() -> None:
    agent_package = Path(__file__).parents[2] / "src" / "wumpus" / "agent"
    forbidden_names = {"World", "GeneratedMap", "grid", "entities"}

    for module_path in agent_package.glob("*.py"):
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(
                    not alias.name.startswith("wumpus.environment")
                    for alias in node.names
                )
            if isinstance(node, ast.ImportFrom):
                assert not (node.module or "").startswith("wumpus.environment")
                assert not (
                    node.module == "wumpus"
                    and any(alias.name == "environment" for alias in node.names)
                )
            if isinstance(node, ast.Name):
                assert node.id not in forbidden_names
            if isinstance(node, ast.Attribute):
                assert node.attr not in forbidden_names
