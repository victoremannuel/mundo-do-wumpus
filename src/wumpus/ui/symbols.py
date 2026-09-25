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
