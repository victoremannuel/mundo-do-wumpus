"""Single source of truth for console colors and symbols (sections 63-64)."""

from types import MappingProxyType

from wumpus.domain import Direction


AGENT_COLOR = "cyan"
SAFE_COLOR = "green"
VISITED_COLOR = "bright_green"
UNKNOWN_COLOR = "dim white"
POSSIBLE_DANGER_COLOR = "yellow"
GLITTER_COLOR = "bright_yellow"
WUMPUS_COLOR = "magenta"
PIT_COLOR = "red"
BAT_COLOR = "blue"
GOLD_COLOR = "bright_yellow"

AGENT_SYMBOLS = MappingProxyType(
    {
        Direction.NORTH: "A↑",
        Direction.EAST: "A→",
        Direction.SOUTH: "A↓",
        Direction.WEST: "A←",
    }
)

DIRECTION_LABELS = MappingProxyType(
    {
        Direction.NORTH: "Norte ↑",
        Direction.EAST: "Leste →",
        Direction.SOUTH: "Sul ↓",
        Direction.WEST: "Oeste ←",
    }
)

SAFE_SYMBOL = "✓"
UNKNOWN_SYMBOL = "?"
RISK_SYMBOL = "!"
WUMPUS_SYMBOL = "W"
PIT_SYMBOL = "P"
BAT_SYMBOL = "B"
GOLD_SYMBOL = "G"
EMPTY_SYMBOL = "."


# ---------------------------------------------------------------------------
# Retro TUI palette (UI-RETRO-TUI-001).
#
# The legacy console palette above stays untouched; these entries extend the
# same single source of truth with the darker, higher-contrast values the
# persistent pixel-art interface needs. Color communicates state -- it is never
# decoration.
# ---------------------------------------------------------------------------

RETRO_BACKGROUND = "#06080f"
RETRO_PANEL_BACKGROUND = "#0a0e1a"
RETRO_BORDER = "#3a4a6b"
RETRO_BORDER_ACTIVE = "#5f7bb0"
RETRO_TEXT = "#d7dce8"
RETRO_TEXT_DIM = "#6b7893"
RETRO_DEBUG = "#ff5fd2"

RETRO_BORDER_STYLE = RETRO_BORDER
RETRO_COORD_STYLE = RETRO_TEXT_DIM
RETRO_LABEL_STYLE = RETRO_TEXT_DIM
RETRO_VALUE_STYLE = f"bold {RETRO_TEXT}"

RETRO_AGENT_STYLE = "bold bright_cyan"
RETRO_SAFE_STYLE = "green"
RETRO_VISITED_STYLE = "bright_green"
RETRO_UNKNOWN_STYLE = "grey37"
RETRO_RISK_STYLE = "yellow"
RETRO_WUMPUS_STYLE = "bold magenta"
RETRO_DEAD_WUMPUS_STYLE = "grey50"
RETRO_PIT_STYLE = "bold red"
RETRO_BAT_STYLE = "bold blue"
RETRO_GOLD_STYLE = "bold bright_yellow"
RETRO_EMPTY_STYLE = "grey30"

RETRO_SENSOR_ON_STYLES = MappingProxyType(
    {
        "FEDOR": RETRO_WUMPUS_STYLE,
        "BRISA": RETRO_PIT_STYLE,
        "MORCEGO": RETRO_BAT_STYLE,
        "BRILHO": RETRO_GOLD_STYLE,
        "IMPACTO": RETRO_RISK_STYLE,
        "GRITO": RETRO_AGENT_STYLE,
    }
)
RETRO_SENSOR_OFF_STYLE = "grey30"

RETRO_STATUS_STYLES = MappingProxyType(
    {
        "RUNNING": "bold bright_green",
        "PAUSED": "bold yellow",
        "JOGADOR": "bold bright_cyan",
        "FINISHED": "bold bright_cyan",
        "ERROR": "bold red",
    }
)

RETRO_OUTCOME_STYLES = MappingProxyType(
    {
        "ESCAPED": "bold bright_green",
        "DEAD": "bold red",
        "TURN_LIMIT": "bold yellow",
    }
)

RETRO_SENSOR_INDICATOR = "●"


# ---------------------------------------------------------------------------
# Animation palette (GAMEPLAY-TUI-ANIMATION-MANUAL-002).
#
# Animations decorate events the game already reported, so their colours reuse
# the meaning the board already assigns: gold stays gold, the Wumpus stays
# magenta, a pit stays red. Nothing here is chosen at random.
# ---------------------------------------------------------------------------

RETRO_TRAIL_STYLE = "cyan"
RETRO_AGENT_HOT_STYLE = "bold bright_white"
RETRO_BEAM_STYLE = "bold bright_white"
RETRO_DEATH_STYLE = "bold red"
RETRO_ESCAPE_STYLE = "bold bright_green"
RETRO_BANNER_STYLE = "bold bright_yellow"

RETRO_GLITCH_STYLES = ("bold blue", "bold magenta")

RETRO_BORDER_ALERT = "#ff4d4d"
RETRO_BORDER_GOLD = "#ffd24d"
RETRO_BORDER_WUMPUS = "#ff5fd2"
RETRO_BORDER_BAT = "#6f7bff"
RETRO_BORDER_ESCAPE = "#4dff88"
RETRO_BORDER_IMPACT = "#ffffff"
