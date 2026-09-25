"""Adapter that lets a human play through the unchanged game loop.

Why this exists
---------------
Manual play must not become a second game loop. `GameEngine` already owns the
perceive -> decide -> act -> learn cycle, and `World.execute` already owns every
rule and score. So the interface never executes an action itself: it *queues*
the key the player pressed, and the engine then asks this object to decide, the
same way it asks `SimpleAgent`. Environment rules, scoring, and terminal
conditions therefore keep exactly one source of truth.

What a human is allowed to know
-------------------------------
`HumanAgent` keeps the same agent-side surface the interface already reads --
`memory`, `actions_taken`, `last_reason` -- and nothing else. It never receives
the world, a generated map, or a hidden entity, and it deliberately runs **no**
inference: the player, not the program, has to interpret stench, breeze, bat
noise, glitter, bump, and scream. Its knowledge base therefore only ever records
what the player has directly seen: rooms visited and rooms proven safe by being
stood in.
"""

from __future__ import annotations

from wumpus.agent.knowledge import KnowledgeBase
from wumpus.agent.memory import AgentMemory
from wumpus.agent.reasoning import DecisionReason
from wumpus.domain import Action, ActionResult, AgentObservation
from wumpus.game.config import GameConfig, START_DIRECTION, START_POSITION


MANUAL_REASON = "Ação selecionada pelo jogador"


class NoPendingActionError(RuntimeError):
    """Raised when the engine asks for a decision the player has not made.

    A turn must never be invented on the player's behalf, so this is an error
    rather than a silently substituted default action.
    """


class HumanAgent:
    """Turn one queued player command into exactly one engine decision."""

    def __init__(self, config: GameConfig | None = None) -> None:
        game_config = config if config is not None else GameConfig()
        self._memory = AgentMemory(
            START_POSITION,
            START_DIRECTION,
            KnowledgeBase(game_config.rows, game_config.cols),
        )
        self._pending_action: Action | None = None
        self._last_reason: DecisionReason | None = None

    # ------------------------------------------------------------------
    # The surface the interface is allowed to read
    # ------------------------------------------------------------------

    @property
    def memory(self) -> AgentMemory:
        return self._memory

    @property
    def actions_taken(self) -> int:
        return len(self._memory.actions)

    @property
    def last_reason(self) -> DecisionReason | None:
        return self._last_reason

    @property
    def pending_action(self) -> Action | None:
        """The command waiting for the next engine step, if any."""

        return self._pending_action

    @property
    def has_pending_action(self) -> bool:
        return self._pending_action is not None

    # ------------------------------------------------------------------
    # Command queue
    # ------------------------------------------------------------------

    def queue_action(self, action: Action) -> None:
        """Accept the command the player just chose for the next turn."""

        self._pending_action = action

    def clear_pending_action(self) -> None:
        """Forget an unplayed command, so a restart cannot leak one turn."""

        self._pending_action = None

    # ------------------------------------------------------------------
    # The contract `GameEngine` requires
    # ------------------------------------------------------------------

    def decide(self, observation: AgentObservation) -> Action:
        """Return exactly the queued command, consuming it."""

        if self._pending_action is None:
            raise NoPendingActionError(
                "A manual turn requires a queued player action"
            )

        self._memory.record_observation(observation)

        action = self._pending_action
        self._pending_action = None
        self._last_reason = DecisionReason(
            action=action,
            reason=MANUAL_REASON,
            target=None,
        )
        return action

    def process_result(self, result: ActionResult) -> None:
        """Remember what happened, without inferring anything from it."""

        self._memory.record_result(result)
