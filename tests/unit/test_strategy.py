from collections import deque

import wumpus.agent.strategy as strategy_module
from wumpus.agent import DecisionReason, KnowledgeBase, Strategy
from wumpus.domain import Action, ActionResult, Direction, EntityType, Perception, Position
from wumpus.game.config import START_POSITION


def shot_result(
    *,
    position: Position,
    direction: Direction,
    wumpus_killed: bool,
    scream: bool,
) -> ActionResult:
    return ActionResult(
        action=Action.SHOOT,
        position=position,
        direction=direction,
        score_delta=-10,
        total_score=-10,
        perception=Perception(
            stench=False,
            breeze=False,
            bat_noise=False,
            glitter=False,
            bump=False,
            scream=scream,
        ),
        wumpus_killed=wumpus_killed,
    )


def safe_knowledge(rows: int, cols: int, safe_cells: list[Position]) -> KnowledgeBase:
    knowledge = KnowledgeBase(rows, cols)
    for cell in safe_cells:
        knowledge.mark_visited(cell)
        knowledge.mark_safe(cell)
    return knowledge


def test_strategy_grabs_gold_regardless_of_the_safe_frontier() -> None:
    knowledge = safe_knowledge(3, 3, [Position(1, 1), Position(1, 2)])
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=True,
    )

    assert action is Action.GRAB
    assert strategy.last_reason == DecisionReason(
        Action.GRAB, "Brilho percebido: coletando ouro", Position(1, 1)
    )


def test_strategy_records_no_reason_before_any_decision() -> None:
    strategy = Strategy()

    assert strategy.last_reason is None


def test_strategy_reasoning_targets_the_pursued_unexplored_cell() -> None:
    knowledge = KnowledgeBase(3, 3)
    knowledge.mark_visited(Position(1, 1))
    knowledge.mark_safe(Position(1, 1))
    knowledge.mark_safe(Position(1, 2))
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    reason = strategy.last_reason
    assert reason is not None
    assert reason.action is action
    assert reason.target == Position(1, 2)


def test_strategy_never_climbs_at_the_start_with_gold_and_no_safe_frontier() -> None:
    knowledge = safe_knowledge(3, 3, [START_POSITION])
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=START_POSITION,
        direction=Direction.NORTH,
        collected_gold=1,
        glitter=False,
    )

    assert action is Action.TURN_RIGHT


def test_strategy_keeps_acting_with_gold_and_no_safe_frontier() -> None:
    """The start room is no longer an escape hatch, so it may not end the turn."""

    knowledge = safe_knowledge(3, 3, [START_POSITION, Position(2, 1), Position(3, 1)])
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(3, 1),
        direction=Direction.NORTH,
        collected_gold=1,
        glitter=False,
    )

    assert action is not Action.CLIMB
    assert action is not None


def test_strategy_explores_the_nearest_unvisited_safe_cell() -> None:
    knowledge = KnowledgeBase(3, 3)
    knowledge.mark_visited(Position(1, 1))
    knowledge.mark_safe(Position(1, 1))
    knowledge.mark_safe(Position(1, 2))
    knowledge.mark_safe(Position(2, 1))
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert action == Action.TURN_RIGHT


def test_strategy_waits_when_no_exit_route_or_exploration_remains() -> None:
    knowledge = safe_knowledge(3, 3, [Position(1, 1)])
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert action is Action.TURN_RIGHT


def test_strategy_reuses_the_queued_plan_across_calls() -> None:
    knowledge = KnowledgeBase(4, 4)
    knowledge.mark_visited(Position(1, 1))
    knowledge.mark_safe(Position(1, 1))
    knowledge.mark_safe(Position(2, 1))
    knowledge.mark_safe(Position(3, 1))
    strategy = Strategy()

    first = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )
    # The caller (AgentMemory, in real use) marks a cell visited once the
    # agent actually arrives there; the test mirrors that before continuing.
    knowledge.mark_visited(Position(2, 1))
    second = strategy.decide(
        knowledge=knowledge,
        position=Position(2, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert first is Action.MOVE_FORWARD
    assert second is Action.MOVE_FORWARD
    assert strategy._target == Position(3, 1)


def test_strategy_replans_after_an_unexpected_teleport() -> None:
    knowledge = KnowledgeBase(4, 4)
    knowledge.mark_visited(Position(1, 1))
    knowledge.mark_safe(Position(1, 1))
    knowledge.mark_safe(Position(2, 1))
    knowledge.mark_safe(Position(3, 1))
    knowledge.mark_visited(Position(1, 3))
    knowledge.mark_safe(Position(1, 3))
    knowledge.mark_safe(Position(1, 2))
    strategy = Strategy()

    strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )
    after_teleport = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 3),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert after_teleport is not None
    assert strategy._path[0] == Position(1, 3)


def test_strategy_replans_after_an_unexpected_bump() -> None:
    knowledge = KnowledgeBase(4, 4)
    knowledge.mark_visited(Position(1, 1))
    knowledge.mark_safe(Position(1, 1))
    knowledge.mark_safe(Position(2, 1))
    strategy = Strategy()

    first = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )
    assert first is Action.MOVE_FORWARD

    repeated = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert repeated is Action.MOVE_FORWARD


def test_strategy_target_selection_is_deterministic() -> None:
    knowledge = KnowledgeBase(3, 3)
    knowledge.mark_visited(Position(1, 1))
    knowledge.mark_safe(Position(1, 1))
    knowledge.mark_safe(Position(1, 2))
    knowledge.mark_safe(Position(2, 1))

    first = Strategy().decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )
    second = Strategy().decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert first == second


def test_strategy_skips_an_unreachable_target_for_a_reachable_one() -> None:
    # Two safe regions separated by an unclassified gap (e.g. after a bat
    # teleport): the nearer candidate by raw distance is not connected
    # through safe cells, so the strategy must fall back to the farther,
    # actually reachable one instead of giving up.
    knowledge = KnowledgeBase(10, 1)
    knowledge.mark_visited(Position(7, 1))
    knowledge.mark_safe(Position(7, 1))
    knowledge.mark_visited(Position(8, 1))
    knowledge.mark_safe(Position(8, 1))
    knowledge.mark_safe(Position(9, 1))  # reachable, distance 2
    knowledge.mark_safe(Position(5, 1))  # unreachable, distance 2, nearer by tie-break
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(7, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert action is not None
    assert strategy._target == Position(9, 1)


def test_strategy_falls_through_to_risk_when_every_unexplored_cell_is_unreachable() -> None:
    # (2, 1) is a "safe" unexplored cell, but the gap at (3, 1)/(4, 1) is
    # fully unclassified, so no safe route reaches it. Priorities 3/4 must
    # not swallow the turn: priority 6 should still take the reachable,
    # in-threshold risk candidate at (6, 1) instead of giving up.
    knowledge = KnowledgeBase(10, 1)
    knowledge.mark_visited(Position(5, 1))
    knowledge.mark_safe(Position(5, 1))
    knowledge.mark_safe(Position(2, 1))
    knowledge.mark_possible(Position(6, 1), EntityType.BAT)
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(5, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert action is not None
    assert strategy._target == Position(6, 1)


def test_strategy_falls_through_to_risk_when_the_way_to_the_exit_is_blocked() -> None:
    # The agent holds gold and has nothing left proven-safe to explore, but
    # the route on to the far-corner exit is broken by an unclassified gap.
    # Priority 2 must not give up outright: a reachable, in-threshold risk
    # candidate should still be taken to try to clear the way.
    knowledge = KnowledgeBase(10, 1)
    knowledge.mark_visited(START_POSITION)
    knowledge.mark_safe(START_POSITION)
    knowledge.mark_visited(Position(5, 1))
    knowledge.mark_safe(Position(5, 1))
    knowledge.mark_possible(Position(6, 1), EntityType.BAT)
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(5, 1),
        direction=Direction.NORTH,
        collected_gold=1,
        glitter=False,
    )

    assert action is not None
    assert strategy._target == Position(6, 1)


def test_strategy_accepts_less_risk_after_collecting_gold() -> None:
    without_gold = safe_knowledge(10, 1, [Position(5, 1)])
    without_gold.mark_possible(Position(6, 1), EntityType.PIT)
    exploratory = Strategy()

    exploratory_action = exploratory.decide(
        knowledge=without_gold,
        position=Position(5, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    with_gold = safe_knowledge(10, 1, [START_POSITION, Position(5, 1)])
    with_gold.mark_possible(Position(6, 1), EntityType.PIT)
    preserving = Strategy()
    preserving_action = preserving.decide(
        knowledge=with_gold,
        position=Position(5, 1),
        direction=Direction.NORTH,
        collected_gold=1,
        glitter=False,
    )

    assert exploratory_action is not None
    assert exploratory._target == Position(6, 1)
    assert preserving_action is Action.TURN_RIGHT
    assert preserving._target is None


def test_strategy_utility_rejects_bat_risk_after_two_gold() -> None:
    knowledge = safe_knowledge(10, 1, [START_POSITION, Position(5, 1)])
    knowledge.mark_possible(Position(6, 1), EntityType.BAT)
    strategy = Strategy(total_gold=3)

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(5, 1),
        direction=Direction.NORTH,
        collected_gold=2,
        glitter=False,
    )

    assert action is Action.TURN_RIGHT
    assert strategy._target is None


def test_strategy_climbs_at_its_configured_exit_after_all_configured_gold() -> None:
    knowledge = safe_knowledge(3, 3, [START_POSITION])
    knowledge.mark_safe(Position(2, 1))
    strategy = Strategy(
        total_gold=3, exit_position=START_POSITION,
    )

    action = strategy.decide(
        knowledge=knowledge,
        position=START_POSITION,
        direction=Direction.NORTH,
        collected_gold=3,
        glitter=False,
    )

    assert action is Action.CLIMB


def test_strategy_returns_to_its_configured_exit_with_all_configured_gold() -> None:
    knowledge = safe_knowledge(
        3,
        3,
        [START_POSITION, Position(2, 1), Position(3, 1)],
    )
    knowledge.mark_safe(Position(3, 2))
    strategy = Strategy(
        total_gold=3, exit_position=START_POSITION,
    )

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(3, 1),
        direction=Direction.NORTH,
        collected_gold=3,
        glitter=False,
    )

    assert action is Action.TURN_RIGHT
    assert strategy._target == START_POSITION


def test_strategy_ignores_an_unsafe_cell_that_is_not_reachable() -> None:
    # (5, 5) is a possible-pit candidate, but it is not adjacent to any cell
    # reachable from (1, 1) through proven-safe cells, so it is never a
    # valid priority-6 target; with nothing else to do, the exit policy
    # deliberately abandons exploration from the start cell.
    knowledge = safe_knowledge(5, 5, [Position(1, 1)])
    knowledge.mark_possible(Position(5, 5), EntityType.PIT)
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert action is Action.TURN_RIGHT


def test_strategy_shoots_a_confirmed_wumpus_once_already_aligned() -> None:
    knowledge = safe_knowledge(3, 3, [Position(1, 1)])
    knowledge.mark_confirmed(Position(1, 3), EntityType.WUMPUS)
    strategy = Strategy()

    first = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )
    # Simulate the turn from `first` having been applied by the environment.
    second = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.EAST,
        collected_gold=0,
        glitter=False,
    )

    assert first is Action.TURN_RIGHT
    assert second is Action.SHOOT


def test_strategy_does_not_shoot_a_merely_possible_wumpus() -> None:
    knowledge = safe_knowledge(3, 3, [Position(1, 1)])
    knowledge.mark_possible(Position(1, 3), EntityType.WUMPUS)
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert action is Action.TURN_RIGHT
    assert action is not Action.SHOOT


def test_strategy_routes_to_an_alignment_cell_before_shooting() -> None:
    # (1,2) and (1,3) are already explored (no longer a "frontier"), but
    # (1,3) shares a column with the Wumpus at (3,3), so it is a valid
    # firing position even though the agent starts unaligned.
    knowledge = safe_knowledge(3, 3, [Position(1, 1), Position(1, 2), Position(1, 3)])
    knowledge.mark_confirmed(Position(3, 3), EntityType.WUMPUS)
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert action is not None
    assert action is not Action.SHOOT
    assert strategy._target == Position(1, 3)


def test_strategy_confirm_kill_marks_the_targeted_wumpus_dead() -> None:
    knowledge = KnowledgeBase(3, 3)
    knowledge.mark_visited(Position(1, 1))
    knowledge.mark_safe(Position(1, 1))
    # The cell between the shooter and the target must be *proven*
    # Wumpus-free, not merely unclassified, for attribution to be sound.
    knowledge.mark_not(Position(1, 2), EntityType.WUMPUS)
    knowledge.mark_confirmed(Position(1, 3), EntityType.WUMPUS)
    strategy = Strategy()
    strategy._target = Position(1, 3)

    strategy.confirm_kill(
        knowledge,
        shot_result(
            position=Position(1, 1),
            direction=Direction.EAST,
            wumpus_killed=True,
            scream=True,
        ),
    )

    assert Position(1, 3) in knowledge.dead_wumpus
    assert Position(1, 3) not in knowledge.confirmed_wumpus
    assert strategy._target is None


def test_strategy_confirm_kill_leaves_an_ambiguous_kill_unresolved() -> None:
    # A closer, merely possible Wumpus candidate sits between the shooter
    # and the confirmed target on the same line: the agent's own knowledge
    # cannot tell which one the arrow actually hit.
    knowledge = KnowledgeBase(5, 1)
    knowledge.mark_visited(Position(1, 1))
    knowledge.mark_safe(Position(1, 1))
    knowledge.mark_confirmed(Position(4, 1), EntityType.WUMPUS)
    knowledge.mark_possible(Position(2, 1), EntityType.WUMPUS)
    strategy = Strategy()
    strategy._target = Position(4, 1)

    strategy.confirm_kill(
        knowledge,
        shot_result(
            position=Position(1, 1),
            direction=Direction.NORTH,
            wumpus_killed=True,
            scream=True,
        ),
    )

    assert Position(4, 1) not in knowledge.dead_wumpus
    assert Position(4, 1) in knowledge.confirmed_wumpus


def test_strategy_confirm_kill_clears_the_cache_even_on_a_miss() -> None:
    knowledge = KnowledgeBase(3, 3)
    strategy = Strategy()
    strategy._target = Position(1, 3)
    strategy._path = [Position(1, 1)]
    strategy._actions = deque([Action.SHOOT])

    strategy.confirm_kill(
        knowledge,
        shot_result(
            position=Position(1, 1),
            direction=Direction.EAST,
            wumpus_killed=False,
            scream=False,
        ),
    )

    assert strategy._target is None
    assert strategy._path == []
    assert strategy._actions == deque()


def test_strategy_confirm_kill_does_not_attribute_through_an_unclassified_cell() -> None:
    # An unvisited cell the agent has never gathered evidence about is not
    # proof it is empty. The real environment stops at the first LIVE
    # Wumpus regardless of what the agent knows, so an undiscovered Wumpus
    # could legitimately be hiding in that unclassified cell and be the one
    # that actually died -- attributing the kill to the farther, confirmed
    # target would then falsely mark a still-alive Wumpus as dead and safe.
    knowledge = KnowledgeBase(5, 1)
    knowledge.mark_visited(Position(1, 1))
    knowledge.mark_safe(Position(1, 1))
    knowledge.mark_confirmed(Position(4, 1), EntityType.WUMPUS)
    # Position(2, 1) and Position(3, 1) are left fully unclassified.
    strategy = Strategy()
    strategy._target = Position(4, 1)

    strategy.confirm_kill(
        knowledge,
        shot_result(
            position=Position(1, 1),
            direction=Direction.NORTH,
            wumpus_killed=True,
            scream=True,
        ),
    )

    assert Position(4, 1) not in knowledge.dead_wumpus
    assert Position(4, 1) in knowledge.confirmed_wumpus


def test_strategy_prioritizes_the_lowest_scoring_risk_candidate() -> None:
    # (2, 1) is a possible-pit candidate (score 3); (1, 2) is a
    # possible-bat candidate (score 2). Priority 6 must prefer the cheaper
    # one even though it is not the nearer one by plain distance ordering.
    knowledge = safe_knowledge(3, 3, [Position(1, 1)])
    knowledge.mark_possible(Position(2, 1), EntityType.PIT)
    knowledge.mark_possible(Position(1, 2), EntityType.BAT)
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert action is not None
    assert strategy._target == Position(1, 2)


def test_strategy_steps_into_the_chosen_risk_candidate_after_turning() -> None:
    knowledge = safe_knowledge(3, 3, [Position(1, 1)])
    knowledge.mark_possible(Position(1, 2), EntityType.BAT)
    strategy = Strategy()

    first = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )
    # Simulate the turn from `first` having been applied by the environment.
    second = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.EAST,
        collected_gold=0,
        glitter=False,
    )

    assert first is Action.TURN_RIGHT
    assert second is Action.MOVE_FORWARD


def test_strategy_prices_a_risk_approach_route_that_contains_a_turn() -> None:
    knowledge = safe_knowledge(
        3,
        3,
        [Position(1, 1), Position(2, 1), Position(2, 2)],
    )
    knowledge.mark_possible(Position(2, 3), EntityType.BAT)
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert action is Action.MOVE_FORWARD
    assert strategy._target == Position(2, 3)
    assert strategy._approach_action_count(
        knowledge,
        Position(1, 1),
        Direction.NORTH,
        Position(2, 3),
    ) == 4
    assert Position(1, 1).manhattan_distance(Position(2, 3)) == 3


def test_strategy_hunting_passes_the_canonical_arrow_cost_to_utility(
    monkeypatch,
) -> None:
    calls: list[dict[str, object]] = []
    real_should_explore = strategy_module.should_explore

    def recording_policy(**kwargs):
        calls.append(kwargs)
        return real_should_explore(**kwargs)

    monkeypatch.setattr(strategy_module, "should_explore", recording_policy)
    knowledge = safe_knowledge(3, 3, [Position(1, 1)])
    knowledge.mark_confirmed(Position(1, 3), EntityType.WUMPUS)

    Strategy().decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.EAST,
        collected_gold=0,
        glitter=False,
    )

    assert calls
    assert calls[0]["requires_arrow"] is True


def test_strategy_declines_a_risk_above_the_threshold_and_waits() -> None:
    # (3, 1) is a candidate for both a pit and a Wumpus (score 3 + 4 = 7),
    # above `risk.RISK_THRESHOLD` (4): priority 6 must not take that risk,
    # and priority 7 routes back toward the start cell instead.
    knowledge = safe_knowledge(5, 1, [Position(1, 1), Position(2, 1)])
    knowledge.mark_possible(Position(3, 1), EntityType.PIT)
    knowledge.mark_possible(Position(3, 1), EntityType.WUMPUS)
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(2, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert action is not None
    assert strategy._target is None


def test_strategy_never_treats_a_confirmed_danger_cell_as_a_risk_candidate() -> None:
    knowledge = safe_knowledge(3, 1, [Position(1, 1)])
    knowledge.mark_confirmed(Position(2, 1), EntityType.PIT)
    strategy = Strategy()

    action = strategy.decide(
        knowledge=knowledge,
        position=Position(1, 1),
        direction=Direction.NORTH,
        collected_gold=0,
        glitter=False,
    )

    assert action is Action.TURN_RIGHT
