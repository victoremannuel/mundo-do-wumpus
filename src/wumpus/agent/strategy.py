"""Fixed decision hierarchy consuming agent-owned knowledge and the planner.

Implements plan section 44's priorities 1-7:

1. Grab visible gold.
2. Climb at the start cell once holding gold with no safe frontier left, or
   route back toward the start cell first when elsewhere.
3/4. Route toward the nearest reachable, unvisited safe cell.
5. Shoot a confirmed Wumpus once no safe exploration remains (section 54:
   only ever a confirmed Wumpus, never mere suspicion): align directly when
   already sharing a row or column with it (section 55), otherwise route to
   the nearest reachable safe cell that would share one.
6. Once no safe exploration and no shootable confirmed Wumpus remain, step
   into the reachable, not-yet-safe cell with the lowest `risk.cell_risk`
   score, provided it stays within `risk.RISK_THRESHOLD` (sections 42-43).
7. When even the least-risk reachable cell exceeds that threshold (or none
   exists), route back toward the start cell instead of taking the risk.

Priorities 2-4 only *return* early when they actually produce an action;
when routing toward an unexplored cell or back to the start cell finds no
safe path (e.g. an unclassified gap separates a disconnected safe region),
`decide` falls through to priorities 5-7 instead of giving up immediately --
including while holding gold, since section 45's "não existem novas células
alcançáveis com risco aceitável" exit condition and section 48 both
contemplate exactly that risk/reward tradeoff. `risk.RISK_THRESHOLD` itself
stays a single, non-gold-conditioned constant: sections 47-48's differing
risk tolerance before/after gold is FASE 15's "política de saída" scope (see
`DEC-005`), not this priority's own threshold.

`decide` returns ``None`` only when no priority here applies at all -- e.g.
already at the start cell with nothing left to explore or risk -- and the
caller supplies its own fallback for that residual gap (full exit-policy
reasoning, section 45-46, remains FASE 15's scope).
"""

from __future__ import annotations

from collections import deque

from wumpus.agent.knowledge import KnowledgeBase
from wumpus.agent.planner import FORWARD_DELTA, find_path, plan_actions, turns_to_face
from wumpus.agent.risk import RISK_THRESHOLD, least_risk_candidate
from wumpus.domain import Action, ActionResult, Direction, Position
from wumpus.game.config import START_POSITION


class Strategy:
    """Choose one action per cycle, planning routes only through safe cells."""

    def __init__(self) -> None:
        self._target: Position | None = None
        self._path: list[Position] = []
        self._actions: deque[Action] = deque()

    def decide(
        self,
        *,
        knowledge: KnowledgeBase,
        position: Position,
        direction: Direction,
        collected_gold: int,
        glitter: bool,
    ) -> Action | None:
        """Return the next action, or ``None`` when no priority here applies."""

        if glitter:
            self._clear()
            return Action.GRAB

        unexplored = knowledge.safe - knowledge.visited

        if collected_gold > 0 and not unexplored:
            if position == START_POSITION:
                self._clear()
                return Action.CLIMB
            action = self._pursue(knowledge, position, direction, (START_POSITION,))
            if action is not None:
                return action

        elif unexplored:
            candidates = sorted(
                unexplored,
                key=lambda cell: (position.manhattan_distance(cell), cell),
            )
            action = self._pursue(knowledge, position, direction, candidates)
            if action is not None:
                return action

        action = self._hunt(knowledge, position, direction)
        if action is not None:
            return action

        action = self._explore_at_risk(knowledge, position, direction)
        if action is not None:
            return action

        self._clear()
        return None

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
    ) -> Action | None:
        """Priority 5: shoot a confirmed Wumpus once no safer option remains."""

        live_wumpus = sorted(
            knowledge.confirmed_wumpus,
            key=lambda cell: (position.manhattan_distance(cell), cell),
        )
        for wumpus in live_wumpus:
            if position.row == wumpus.row or position.col == wumpus.col:
                return self._fire_at(position, direction, wumpus)

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
            action = self._pursue(knowledge, position, direction, alignment_cells)
            if action is not None:
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
    ) -> Action | None:
        """Priorities 6-7: least-risk step, or forced return when too risky.

        Ordinarily reached with `collected_gold == 0`, since priority 2
        already routes back to the start cell and climbs as soon as the
        agent holds gold with no safe frontier left. It can still be reached
        while holding gold if that return route itself has no safe path
        (`decide` falls through rather than giving up) -- `RISK_THRESHOLD`
        deliberately does not loosen or tighten for that case; see
        `DEC-005`.
        """

        candidate = least_risk_candidate(knowledge, position)
        if candidate is not None and candidate.score <= RISK_THRESHOLD:
            return self._approach(knowledge, position, direction, candidate.position)

        if position == START_POSITION:
            return None
        return self._pursue(knowledge, position, direction, (START_POSITION,))

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
