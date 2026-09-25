from wumpus.agent import DecisionReason
from wumpus.domain import Action, Position


def test_decision_reason_holds_action_text_and_optional_target() -> None:
    reason = DecisionReason(Action.MOVE_FORWARD, "Safe unexplored frontier", Position(4, 2))

    assert reason.action is Action.MOVE_FORWARD
    assert reason.reason == "Safe unexplored frontier"
    assert reason.target == Position(4, 2)


def test_decision_reason_target_defaults_to_none() -> None:
    reason = DecisionReason(Action.TURN_RIGHT, "Waiting for new evidence")

    assert reason.target is None


def test_decision_reason_accepts_no_action_for_a_stalled_decision() -> None:
    reason = DecisionReason(None, "No safe or acceptable action available")

    assert reason.action is None
