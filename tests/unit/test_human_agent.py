"""Manual decisions still travel through the unchanged engine agent contract."""

import ast
from pathlib import Path

import pytest

from wumpus.agent import HumanAgent, NoPendingActionError
from wumpus.agent.human_agent import MANUAL_REASON
from wumpus.domain import (
    Action,
    ActionResult,
    AgentObservation,
    Direction,
    Perception,
    Position,
)


EMPTY_PERCEPTION = Perception(False, False, False, False, False, False)


def observation() -> AgentObservation:
    return AgentObservation(
        position=Position(1, 1), direction=Direction.NORTH,
        perception=EMPTY_PERCEPTION, score=0, collected_gold=0, active=True,
    )


def result(action: Action) -> ActionResult:
    return ActionResult(
        action=action, position=Position(1, 1), direction=Direction.NORTH,
        score_delta=-1, total_score=-1, perception=EMPTY_PERCEPTION,
    )


def test_human_agent_requires_and_consumes_exactly_one_queued_action() -> None:
    agent = HumanAgent()
    assert agent.pending_action is None
    with pytest.raises(NoPendingActionError, match="queued player action"):
        agent.decide(observation())

    agent.queue_action(Action.MOVE_FORWARD)
    assert agent.has_pending_action
    assert agent.decide(observation()) is Action.MOVE_FORWARD
    assert agent.pending_action is None
    assert len(agent.memory.perception_history) == 1
    assert agent.last_reason is not None
    assert agent.last_reason.reason == MANUAL_REASON
    assert agent.last_reason.target is None


def test_human_agent_records_results_without_running_inference() -> None:
    agent = HumanAgent()
    agent.queue_action(Action.TURN_LEFT)
    chosen = agent.decide(observation())
    agent.process_result(result(chosen))

    assert agent.actions_taken == 1
    assert agent.memory.actions == (Action.TURN_LEFT,)
    assert not hasattr(agent, "inference")


def test_human_agent_has_no_environment_or_hidden_map_dependency() -> None:
    path = Path(__file__).parents[2] / "src/wumpus/agent/human_agent.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert not (node.module or "").startswith("wumpus.environment")
        if isinstance(node, ast.Name):
            assert node.id not in {"World", "GeneratedMap"}
