"""Fixed decision hierarchy consuming agent-owned knowledge and the planner.

Implements plan section 44's priorities 1-4:

1. Grab visible gold.
2. Climb at the start cell once holding gold with no safe frontier left, or
   route back toward the start cell first when elsewhere.
3/4. Route toward the nearest reachable, unvisited safe cell.

Priority 5 (shoot a confirmed Wumpus blocking a useful route) requires the
alignment and firing mechanics built in FASE 13 — Wumpus hunting. Priorities
6-7 (least-risk fallback and forced return under excessive risk) require the
FASE 14 — Risk engine. Both are intentionally out of scope here; `decide`
returns ``None`` when no priority in this phase applies, and the caller
supplies its own temporary fallback until those phases exist.
"""

from __future__ import annotations

from collections import deque

from wumpus.agent.knowledge import KnowledgeBase
from wumpus.agent.planner import find_path, plan_actions
from wumpus.domain import Action, Direction, Position
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
            return self._pursue(knowledge, position, direction, (START_POSITION,))

        if unexplored:
            candidates = sorted(
                unexplored,
                key=lambda cell: (position.manhattan_distance(cell), cell),
            )
            return self._pursue(knowledge, position, direction, candidates)

        self._clear()
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
