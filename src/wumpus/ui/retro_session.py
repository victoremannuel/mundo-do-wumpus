"""The contract between the composition root and the interface.

The interface now creates games instead of merely displaying one: a player picks
a mode and a cave configuration, starts a match, and may restart into a new one.
That work still must not move into `wumpus.ui`, which is not allowed to know
about the world, the generator, or the agent implementations.

So the interface only ever holds a `SessionFactory`: a callable owned by the
composition root that turns `SessionSettings` into a ready `GameSession`. The
session exposes the engine to drive, the agent-owned presentation surface to
read, the first observation, and -- for professor mode only -- an already
authorized debug view source. The real `World` never appears here.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from enum import Enum, auto

from wumpus.domain import Action, AgentObservation
from wumpus.game.config import GameConfig, available_entity_cells, resolve_effective_seed
from wumpus.game.engine import GameEngine
from wumpus.game.objective import GameObjective
from wumpus.ui.retro_state import AgentPresentationSource, MapView


DebugMapSource = Callable[[], MapView]
ManualActionSubmitter = Callable[[Action], None]
ManualActionClearer = Callable[[], None]


class GameMode(Enum):
    """Who chooses the actions of a match."""

    AUTONOMOUS = auto()
    MANUAL = auto()


MODE_LABELS = {
    GameMode.AUTONOMOUS: "AUTÔNOMO",
    GameMode.MANUAL: "JOGADOR",
}


@dataclass(frozen=True)
class SessionSettings:
    """Everything a player chose before a match is assembled."""

    mode: GameMode
    seed: int | None = None
    game_config: GameConfig | None = None
    objective: GameObjective = GameObjective.COLLECT_ALL_GOLD

    def __post_init__(self) -> None:
        """Freeze a concrete identity before a session is assembled."""

        object.__setattr__(self, "seed", resolve_effective_seed(self.seed))

    @property
    def config(self) -> GameConfig:
        """The configuration to generate with, defaults included."""

        return self.game_config if self.game_config is not None else GameConfig()

    def with_mode(self, mode: GameMode) -> "SessionSettings":
        return replace(self, mode=mode)

    def with_objective(self, objective: GameObjective) -> "SessionSettings":
        return replace(self, objective=objective)


@dataclass(frozen=True)
class GameSession:
    """One assembled match, reduced to what the interface may touch."""

    engine: GameEngine
    presentation_source: AgentPresentationSource
    initial_observation: AgentObservation
    mode: GameMode
    settings: SessionSettings
    debug_map_source: DebugMapSource | None = None
    manual_action_submitter: ManualActionSubmitter | None = None
    manual_action_clearer: ManualActionClearer | None = None

    @property
    def is_manual(self) -> bool:
        return self.mode is GameMode.MANUAL


SessionFactory = Callable[[SessionSettings], GameSession]


# ---------------------------------------------------------------------------
# Configuration validation
#
# The generator validates the same limit as its own second line of defence, but
# the interface has to check first: a player's mistake must become a readable
# message on the setup screen, never a traceback over the game.
# ---------------------------------------------------------------------------

INVALID_CONFIG_TITLE = "CONFIGURAÇÃO INVÁLIDA"


def cave_capacity(config: GameConfig) -> int:
    """How many entities this map size can hold outside the safe start zone."""

    return available_entity_cells(config.rows, config.cols)


def validate_cave(config: GameConfig) -> str | None:
    """Return why this configuration cannot start a game, or `None` if it can."""

    counts = (
        config.wumpus_count,
        config.pit_count,
        config.gold_count,
        config.bat_count,
    )
    if any(
        not isinstance(count, int) or isinstance(count, bool) or count < 0
        for count in counts
    ):
        return "As quantidades devem ser números inteiros maiores ou iguais a 0."

    capacity = cave_capacity(config)
    if config.entity_total > capacity:
        return (
            "A soma das entidades não pode exceder "
            f"{capacity} células disponíveis."
        )
    return None
