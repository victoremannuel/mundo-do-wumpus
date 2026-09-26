"""Functional game loop connecting an environment to a logical agent."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol

from wumpus.domain import Action, ActionResult, AgentObservation, Position
from wumpus.game.config import MAX_TURNS


class GameStatus(Enum):
    """Reason why the loop stopped."""

    ESCAPED = auto()
    DEAD = auto()
    TURN_LIMIT = auto()
    ABANDONED = auto()


class Environment(Protocol):
    """Environment surface the loop is allowed to use."""

    @property
    def agent_position(self) -> Position: ...

    @property
    def score(self) -> int: ...

    @property
    def collected_gold(self) -> int: ...

    @property
    def killed_wumpus(self) -> int: ...

    @property
    def game_over(self) -> bool: ...

    @property
    def escaped(self) -> bool: ...

    @property
    def dead(self) -> bool: ...

    def observation(self) -> AgentObservation: ...

    def execute(self, action: Action) -> ActionResult: ...


class Agent(Protocol):
    """Decision surface required from any agent implementation."""

    def decide(self, observation: AgentObservation) -> Action: ...

    def process_result(self, result: ActionResult) -> None: ...


@dataclass(frozen=True)
class GameOutcome:
    """Final report of one complete game."""

    status: GameStatus
    score: int
    collected_gold: int
    killed_wumpus: int
    turns: int
    visited_cells: int

    @property
    def escaped(self) -> bool:
        return self.status is GameStatus.ESCAPED


TurnRenderer = Callable[[AgentObservation], None]
FinalRenderer = Callable[[GameOutcome], None]


class GameEngine:
    """Drive turns until a terminal condition or the technical turn limit."""

    def __init__(
        self,
        environment: Environment,
        agent: Agent,
        *,
        max_turns: int = MAX_TURNS,
        on_render: TurnRenderer | None = None,
        on_render_final: FinalRenderer | None = None,
    ) -> None:
        if max_turns < 1:
            raise ValueError("max_turns must be at least 1")

        self._environment = environment
        self._agent = agent
        self._max_turns = max_turns
        self._on_render = on_render
        self._on_render_final = on_render_final
        self._turns = 0
        self._visited: set[Position] = {environment.agent_position}

    @property
    def max_turns(self) -> int:
        return self._max_turns

    @property
    def turns(self) -> int:
        return self._turns

    @property
    def visited_cells(self) -> frozenset[Position]:
        return frozenset(self._visited)

    @property
    def is_over(self) -> bool:
        return (
            self._environment.game_over
            or self._agent_abandoned()
            or self._turns >= self._max_turns
        )

    def step(self) -> ActionResult:
        """Run exactly one turn of the perceive-decide-act-learn cycle."""

        if self.is_over:
            raise RuntimeError("Cannot step after the game is over")

        observation = self._environment.observation()
        if self._on_render is not None:
            self._on_render(observation)
        action = self._agent.decide(observation)
        result = self._environment.execute(action)
        self._agent.process_result(result)

        self._turns += 1
        self._visited.add(result.position)
        return result

    def run(self) -> GameOutcome:
        """Run turns until the game ends and return its outcome."""

        while not self.is_over:
            self.step()
        outcome = self.outcome()
        if self._on_render_final is not None:
            self._on_render_final(outcome)
        return outcome

    def outcome(self) -> GameOutcome:
        """Build the final outcome after the game has ended."""

        if not self.is_over:
            raise RuntimeError("Outcome is unavailable before the game is over")

        return GameOutcome(
            status=self._status(),
            score=self._environment.score,
            collected_gold=self._environment.collected_gold,
            killed_wumpus=self._environment.killed_wumpus,
            turns=self._turns,
            visited_cells=len(self._visited),
        )

    def _status(self) -> GameStatus:
        if self._environment.escaped:
            return GameStatus.ESCAPED
        if self._environment.dead:
            return GameStatus.DEAD
        if self._agent_abandoned():
            return GameStatus.ABANDONED
        return GameStatus.TURN_LIMIT

    def _agent_abandoned(self) -> bool:
        """Honor an optional, agent-owned rational-stop signal."""

        return bool(getattr(self._agent, "abandoned", False))
