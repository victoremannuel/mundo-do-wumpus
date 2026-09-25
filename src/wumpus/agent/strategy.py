"""Objective-aware, knowledge-only decisions for the logical agent."""

from __future__ import annotations

from collections import deque

from wumpus.agent.exit_policy import should_explore
from wumpus.agent.knowledge import KnowledgeBase
from wumpus.agent.planner import FORWARD_DELTA, find_path, plan_actions, turns_to_face
from wumpus.agent.reasoning import DecisionReason
from wumpus.agent.risk import least_risk_candidate, least_risk_candidate_toward
from wumpus.domain import Action, ActionResult, Direction, Position
from wumpus.game.config import GameConfig, exit_position_for
from wumpus.game.objective import GameObjective


class Strategy:
    """Choose one action per cycle, planning routes only through safe cells."""

    def __init__(
        self,
        total_gold: int | None = None,
        *,
        objective: GameObjective = GameObjective.COLLECT_ALL_GOLD,
        exit_position: Position | None = None,
    ) -> None:
        configured_gold = GameConfig().gold_count if total_gold is None else total_gold
        if configured_gold < 0:
            raise ValueError("total_gold cannot be negative")
        self._total_gold = configured_gold
        self._objective = objective
        self._exit_position = (
            exit_position
            if exit_position is not None
            else exit_position_for(GameConfig().rows, GameConfig().cols)
        )
        self._target: Position | None = None
        self._path: list[Position] = []
        self._actions: deque[Action] = deque()
        self._last_reason: DecisionReason | None = None

    @property
    def last_reason(self) -> DecisionReason | None:
        """Return the structured explanation for the most recent `decide` call."""

        return self._last_reason

    def decide(
        self,
        *,
        knowledge: KnowledgeBase,
        position: Position,
        direction: Direction,
        collected_gold: int,
        glitter: bool,
    ) -> Action:
        """Return one deterministic action for the configured match objective."""

        if self._objective is GameObjective.ESCAPE_FAST:
            return self._decide_fast_escape(knowledge, position, direction, collected_gold)
        if self._objective is GameObjective.COLLECT_ALL_GOLD:
            return self._decide_collect_all(
                knowledge, position, direction, collected_gold, glitter
            )
        raise AssertionError(f"Unsupported game objective: {self._objective!r}")

    def _decide_collect_all(
        self,
        knowledge: KnowledgeBase,
        position: Position,
        direction: Direction,
        collected_gold: int,
        glitter: bool,
    ) -> Action:
        """Collect every public-count gold, then make the exit the only target."""

        if glitter:
            self._clear()
            self._last_reason = DecisionReason(
                Action.GRAB, "Brilho percebido: coletando ouro", position
            )
            return Action.GRAB

        if collected_gold >= self._total_gold:
            return self._exit_or_wait(knowledge, position, direction)

        unexplored = knowledge.safe - knowledge.visited

        if unexplored:
            candidates = sorted(
                unexplored,
                key=lambda cell: (position.manhattan_distance(cell), cell),
            )
            action = self._pursue(knowledge, position, direction, candidates)
            if action is not None:
                self._last_reason = DecisionReason(
                    action, "Explorando a célula segura mais próxima", self._target
                )
                return action

        action = self._hunt(
            knowledge,
            position,
            direction,
            collected_gold,
        )
        if action is not None:
            return action

        action = self._explore_at_risk(
            knowledge,
            position,
            direction,
            collected_gold,
            fall_back_to_exit=False,
        )
        if action is not None:
            return action

        self._clear()
        self._last_reason = DecisionReason(
            None, "Nenhuma ação segura ou aceitável disponível", None
        )
        return None

    def _decide_fast_escape(
        self,
        knowledge: KnowledgeBase,
        position: Position,
        direction: Direction,
        collected_gold: int,
    ) -> Action:
        """Reach the public exit efficiently without sacrificing known safety."""

        action = self._pursue(
            knowledge, position, direction, (self._exit_position,)
        )
        if action is not None:
            self._last_reason = DecisionReason(
                action, "Rota segura mais curta para a saída", self._exit_position
            )
            return action

        unexplored = knowledge.safe - knowledge.visited
        if unexplored:
            candidates = self._frontier_toward_exit(
                knowledge, position, direction, unexplored
            )
            action = self._pursue(knowledge, position, direction, candidates)
            if action is not None:
                self._last_reason = DecisionReason(
                    action, "Explorando fronteira segura em direção à saída", self._target
                )
                return action

        action = self._hunt(knowledge, position, direction, collected_gold)
        if action is not None:
            return action
        action = self._explore_at_risk(
            knowledge,
            position,
            direction,
            collected_gold,
            fall_back_to_exit=True,
            target_aware=True,
        )
        if action is not None:
            return action
        return self._wait()

    def _frontier_toward_exit(
        self,
        knowledge: KnowledgeBase,
        position: Position,
        direction: Direction,
        candidates: set[Position],
    ) -> tuple[Position, ...]:
        """Order reachable safe frontier by real action cost plus exit distance."""

        ranked: list[tuple[int, int, int, Position]] = []
        for cell in candidates:
            path = find_path(knowledge, position, cell)
            if path is None:
                continue
            action_cost = len(plan_actions(path, direction))
            remaining = cell.manhattan_distance(self._exit_position)
            ranked.append((action_cost + remaining, remaining, action_cost, cell))
        return tuple(item[-1] for item in sorted(ranked))

    def confirm_kill(self, knowledge: KnowledgeBase, result: ActionResult) -> None:
        """Reconcile knowledge after a `SHOOT` result (plan section 56).

        Clears the firing plan unconditionally -- a shot is new information
        either way. When it killed a Wumpus, the death is only attributed to
        this strategy's own confirmed target if every cell strictly closer
        along the exact line of fire is already *proven* Wumpus-free
        (`knowledge.not_wumpus`). A cell the agent has simply never gathered
        evidence about is not proof of absence -- the real arrow could have
        struck an undiscovered Wumpus hiding there instead, since the real
        environment stops at the first *live* Wumpus regardless of what the
        agent has or has not observed. Otherwise which Wumpus died cannot be
        determined from the agent's own knowledge, and no unproven cell is
        marked dead.
        """

        target = self._target
        self._clear()
        if not result.wumpus_killed or target is None:
            return

        for cell in self._line_of_fire(knowledge, result.position, result.direction):
            if cell == target:
                knowledge.mark_wumpus_dead(target)
                return
            if cell not in knowledge.not_wumpus:
                return

    def _hunt(
        self,
        knowledge: KnowledgeBase,
        position: Position,
        direction: Direction,
        collected_gold: int,
    ) -> Action | None:
        """Priority 5: shoot a confirmed Wumpus once no safer option remains."""

        live_wumpus = sorted(
            knowledge.confirmed_wumpus,
            key=lambda cell: (position.manhattan_distance(cell), cell),
        )
        for wumpus in live_wumpus:
            if position.row == wumpus.row or position.col == wumpus.col:
                required = self._direction_towards(position, wumpus)
                if not should_explore(
                    candidate_risk=0.0,
                    movement_actions=len(turns_to_face(direction, required)),
                    collected_gold=collected_gold,
                    total_gold=self._total_gold,
                    requires_arrow=True,
                ):
                    return None
                action = self._fire_at(position, direction, wumpus)
                self._last_reason = DecisionReason(
                    action, "Atirando no Wumpus confirmado alinhado", wumpus
                )
                return action

            alignment_cells = sorted(
                (
                    cell
                    for cell in knowledge.safe
                    if cell.row == wumpus.row or cell.col == wumpus.col
                ),
                key=lambda cell: (position.manhattan_distance(cell), cell),
            )
            if not alignment_cells:
                continue
            alignment_cost = self._alignment_action_count(
                knowledge,
                position,
                direction,
                alignment_cells,
                wumpus,
            )
            if alignment_cost is None or not should_explore(
                candidate_risk=0.0,
                movement_actions=alignment_cost,
                collected_gold=collected_gold,
                total_gold=self._total_gold,
                requires_arrow=True,
            ):
                continue
            action = self._pursue(knowledge, position, direction, alignment_cells)
            if action is not None:
                self._last_reason = DecisionReason(
                    action,
                    "Alinhando-se para atirar no Wumpus confirmado",
                    wumpus,
                )
                return action

        return None

    def _fire_at(
        self,
        position: Position,
        direction: Direction,
        wumpus: Position,
    ) -> Action | None:
        if not self._is_plan_valid(wumpus, position):
            required = self._direction_towards(position, wumpus)
            self._target = wumpus
            self._path = [position]
            self._actions = deque(turns_to_face(direction, required))
            self._actions.append(Action.SHOOT)
        return self._advance()

    @staticmethod
    def _direction_towards(position: Position, target: Position) -> Direction:
        if position.row == target.row:
            return Direction.EAST if target.col > position.col else Direction.WEST
        return Direction.NORTH if target.row > position.row else Direction.SOUTH

    @staticmethod
    def _line_of_fire(
        knowledge: KnowledgeBase,
        origin: Position,
        direction: Direction,
    ) -> tuple[Position, ...]:
        row_step, col_step = FORWARD_DELTA[direction]
        cells: list[Position] = []
        cell = Position(origin.row + row_step, origin.col + col_step)
        while cell in knowledge.all_cells:
            cells.append(cell)
            cell = Position(cell.row + row_step, cell.col + col_step)
        return tuple(cells)

    def _explore_at_risk(
        self,
        knowledge: KnowledgeBase,
        position: Position,
        direction: Direction,
        collected_gold: int,
        *,
        fall_back_to_exit: bool,
        target_aware: bool = False,
    ) -> Action | None:
        """Take an acceptable least-risk step or deliberately abandon."""

        candidate = (
            least_risk_candidate_toward(knowledge, position, self._exit_position)
            if target_aware
            else least_risk_candidate(knowledge, position)
        )
        if candidate is not None:
            action_count = self._approach_action_count(
                knowledge,
                position,
                direction,
                candidate.position,
            )
            if action_count is not None and should_explore(
                candidate_risk=candidate.score,
                movement_actions=action_count,
                collected_gold=collected_gold,
                total_gold=self._total_gold,
            ):
                action = self._approach(
                    knowledge,
                    position,
                    direction,
                    candidate.position,
                )
                self._last_reason = DecisionReason(
                    action,
                    f"Aceitando risco calculado ({candidate.score:.2f}) "
                    "dentro da tolerância",
                    candidate.position,
                )
                return action

        if fall_back_to_exit:
            return self._exit_or_wait(knowledge, position, direction)
        return self._wait()

    def _exit_or_wait(
        self,
        knowledge: KnowledgeBase,
        position: Position,
        direction: Direction,
    ) -> Action:
        """Navigate safely to the automatic exit, or wait without guessing."""

        action = self._pursue(knowledge, position, direction, (self._exit_position,))
        if action is not None:
            self._last_reason = DecisionReason(
                action,
                "Objetivo cumprido: navegando para a saída",
                self._exit_position,
            )
            return action
        return self._wait()

    def _wait(self) -> Action:
        self._clear()
        self._last_reason = DecisionReason(
            Action.TURN_RIGHT,
            "Nenhuma rota segura conhecida; aguardando em posição",
            None,
        )
        return Action.TURN_RIGHT

    def _approach_action_count(
        self,
        knowledge: KnowledgeBase,
        position: Position,
        direction: Direction,
        target: Position,
    ) -> int | None:
        """Return the exact action count for the best safe approach plan."""

        staging_cells = sorted(
            (cell for cell in knowledge.safe if target in cell.neighbors()),
            key=lambda cell: (position.manhattan_distance(cell), cell),
        )
        for staging in staging_cells:
            path = find_path(knowledge, position, staging)
            if path is None:
                continue
            actions = plan_actions(path, direction)
            final_direction = (
                self._direction_towards(path[-2], path[-1])
                if len(path) > 1
                else direction
            )
            required = self._direction_towards(staging, target)
            return len(actions) + len(turns_to_face(final_direction, required)) + 1
        return None

    def _alignment_action_count(
        self,
        knowledge: KnowledgeBase,
        position: Position,
        direction: Direction,
        candidates: tuple[Position, ...] | list[Position],
        wumpus: Position,
    ) -> int | None:
        """Count route and final facing actions for a firing position."""

        for target in candidates:
            path = find_path(knowledge, position, target)
            if path is not None:
                actions = plan_actions(path, direction)
                final_direction = (
                    self._direction_towards(path[-2], path[-1])
                    if len(path) > 1
                    else direction
                )
                required = self._direction_towards(target, wumpus)
                return len(actions) + len(turns_to_face(final_direction, required))
        return None

    def _approach(
        self,
        knowledge: KnowledgeBase,
        position: Position,
        direction: Direction,
        target: Position,
    ) -> Action | None:
        """Route to a safe cell adjacent to ``target``, then step into it.

        `find_path` only routes through cells already proven safe, so it
        cannot reach ``target`` itself (a risk candidate, by definition not
        yet proven safe). The final `MOVE_FORWARD` into ``target`` is the
        calculated risk itself.
        """

        if self._is_plan_valid(target, position):
            return self._advance()

        staging_cells = sorted(
            (cell for cell in knowledge.safe if target in cell.neighbors()),
            key=lambda cell: (position.manhattan_distance(cell), cell),
        )
        for staging in staging_cells:
            path = find_path(knowledge, position, staging)
            if path is None:
                continue
            last_direction = (
                self._direction_towards(path[-2], path[-1])
                if len(path) > 1
                else direction
            )
            required = self._direction_towards(staging, target)
            self._target = target
            self._path = [*path, target]
            self._actions = plan_actions(path, direction)
            self._actions.extend(turns_to_face(last_direction, required))
            self._actions.append(Action.MOVE_FORWARD)
            return self._advance()

        return None

    def _pursue(
        self,
        knowledge: KnowledgeBase,
        position: Position,
        direction: Direction,
        candidates: tuple[Position, ...] | list[Position],
    ) -> Action | None:
        """Continue the cached route, or adopt the nearest reachable candidate.

        A cell can be classified ``safe`` without being connected to the
        agent's current position through other ``safe`` cells yet -- for
        example two regions separated by an unclassified gap after a bat
        teleport. Candidates are tried nearest-first and skipped when
        unreachable, instead of giving up on the first (possibly isolated)
        pick.
        """

        if (
            self._target is not None
            and self._target in candidates
            and self._is_plan_valid(self._target, position)
        ):
            return self._advance()

        for target in candidates:
            path = find_path(knowledge, position, target)
            if path is not None:
                self._target = target
                self._path = path
                self._actions = plan_actions(path, direction)
                return self._advance()

        self._clear()
        return None

    def _advance(self) -> Action | None:
        if not self._actions:
            self._clear()
            return None

        action = self._actions.popleft()
        if action is Action.MOVE_FORWARD and len(self._path) > 1:
            self._path.pop(0)
        return action

    def _is_plan_valid(self, target: Position, position: Position) -> bool:
        return (
            self._target == target
            and bool(self._path)
            and self._path[0] == position
            and bool(self._actions)
        )

    def _clear(self) -> None:
        self._target = None
        self._path = []
        self._actions = deque()
