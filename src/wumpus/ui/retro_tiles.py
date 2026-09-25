"""Pixel-art tile engine for the persistent retro terminal interface.

Geometry is fixed and named: every logical room occupies exactly `TILE_HEIGHT`
terminal lines by `TILE_WIDTH` terminal columns. Terminal cells are taller than
they are wide, so a tile is deliberately wider than tall in order to read as a
square room on screen.

Sprites are pure presentation data. They carry no domain decisions, never read
hidden world state, and are drawn only with block/box characters whose visual
width is a single column in every terminal, so the map can never misalign.
"""

from __future__ import annotations

from enum import Enum, auto
from types import MappingProxyType

from wumpus.domain import Direction
from wumpus.ui.symbols import (
    RETRO_AGENT_STYLE,
    RETRO_BAT_STYLE,
    RETRO_DEAD_WUMPUS_STYLE,
    RETRO_EMPTY_STYLE,
    RETRO_GOLD_STYLE,
    RETRO_PIT_STYLE,
    RETRO_RISK_STYLE,
    RETRO_SAFE_STYLE,
    RETRO_UNKNOWN_STYLE,
    RETRO_VISITED_STYLE,
    RETRO_WUMPUS_STYLE,
)


TILE_HEIGHT = 5
TILE_WIDTH = 10


class TileKind(Enum):
    """What a single rendered room depicts, independent of why."""

    UNKNOWN = auto()
    SAFE = auto()
    VISITED = auto()
    RISK = auto()
    WUMPUS = auto()
    DEAD_WUMPUS = auto()
    PIT = auto()
    BAT = auto()
    GOLD = auto()
    EMPTY = auto()
    START = auto()
    EXIT = auto()
    AGENT = auto()


_UNKNOWN_SPRITE = (
    "░░░░░░░░░░",
    "░▒░░░▒░░░░",
    "░░░ ? ░░░░",
    "░░▒░░░░░░░",
    "░░░░░░░░░░",
)

_SAFE_SPRITE = (
    "·        ·",
    "          ",
    "    ·     ",
    "          ",
    "·        ·",
)

_VISITED_SPRITE = (
    "··········",
    "·        ·",
    "·   ··   ·",
    "·        ·",
    "··········",
)

_RISK_SPRITE = (
    "    ██    ",
    "   ████   ",
    "    ██    ",
    "          ",
    "    ██    ",
)

_WUMPUS_SPRITE = (
    " ██    ██ ",
    " ████████ ",
    " ██ ██ ██ ",
    "  ██████  ",
    "   █  █   ",
)

_PIT_SPRITE = (
    "          ",
    "  ░░░░░░  ",
    " ▒▒▒▒▒▒▒▒ ",
    " ████████ ",
    "  ██████  ",
)

_BAT_SPRITE = (
    "██      ██",
    " ███  ███ ",
    "  ██████  ",
    "   ████   ",
    "    ██    ",
)

_GOLD_SPRITE = (
    "    ██    ",
    "   ████   ",
    "  ██████  ",
    "   ████   ",
    "    ██    ",
)

_EMPTY_SPRITE = (
    "          ",
    "          ",
    "    ··    ",
    "          ",
    "          ",
)

_START_SPRITE = (
    "INI      █",
    "  █    █  ",
    "    ██    ",
    "  █    █  ",
    "█        █",
)

_EXIT_SPRITE = (
    "SAI██████ ",
    " ██    ██ ",
    " ██    ██ ",
    " ██    ██ ",
    "  ██████  ",
)

_AGENT_SPRITES = MappingProxyType(
    {
        Direction.NORTH: (
            "    ██    ",
            "   ████   ",
            "  ██████  ",
            " ████████ ",
            "   ████   ",
        ),
        Direction.SOUTH: (
            "   ████   ",
            " ████████ ",
            "  ██████  ",
            "   ████   ",
            "    ██    ",
        ),
        Direction.EAST: (
            " ██       ",
            " ████     ",
            " ████████ ",
            " ████     ",
            " ██       ",
        ),
        Direction.WEST: (
            "       ██ ",
            "     ████ ",
            " ████████ ",
            "     ████ ",
            "       ██ ",
        ),
    }
)

_SPRITES = MappingProxyType(
    {
        TileKind.UNKNOWN: _UNKNOWN_SPRITE,
        TileKind.SAFE: _SAFE_SPRITE,
        TileKind.VISITED: _VISITED_SPRITE,
        TileKind.RISK: _RISK_SPRITE,
        TileKind.WUMPUS: _WUMPUS_SPRITE,
        TileKind.DEAD_WUMPUS: _WUMPUS_SPRITE,
        TileKind.PIT: _PIT_SPRITE,
        TileKind.BAT: _BAT_SPRITE,
        TileKind.GOLD: _GOLD_SPRITE,
        TileKind.EMPTY: _EMPTY_SPRITE,
        TileKind.START: _START_SPRITE,
        TileKind.EXIT: _EXIT_SPRITE,
    }
)

TILE_STYLES = MappingProxyType(
    {
        TileKind.UNKNOWN: RETRO_UNKNOWN_STYLE,
        TileKind.SAFE: RETRO_SAFE_STYLE,
        TileKind.VISITED: RETRO_VISITED_STYLE,
        TileKind.RISK: RETRO_RISK_STYLE,
        TileKind.WUMPUS: RETRO_WUMPUS_STYLE,
        TileKind.DEAD_WUMPUS: RETRO_DEAD_WUMPUS_STYLE,
        TileKind.PIT: RETRO_PIT_STYLE,
        TileKind.BAT: RETRO_BAT_STYLE,
        TileKind.GOLD: RETRO_GOLD_STYLE,
        TileKind.EMPTY: RETRO_EMPTY_STYLE,
        TileKind.START: "bright_cyan",
        TileKind.EXIT: "bright_green",
        TileKind.AGENT: RETRO_AGENT_STYLE,
    }
)


# ---------------------------------------------------------------------------
# Legend icons
#
# The legend has to let a player recognise the *drawing* on the board, not just
# its colour, so every entry carries a miniature of its own sprite built from
# the same characters. Two lines by five columns is the smallest size at which
# the silhouettes stay distinguishable from each other.
# ---------------------------------------------------------------------------

LEGEND_ICON_HEIGHT = 2
LEGEND_ICON_WIDTH = 5

_LEGEND_SPRITES = MappingProxyType(
    {
        TileKind.AGENT: ("██   ", "█████"),
        TileKind.SAFE: ("·   ·", "  ·  "),
        TileKind.VISITED: ("·····", "·····"),
        TileKind.UNKNOWN: ("░░░░░", "░░?░░"),
        TileKind.RISK: ("  ██ ", "  ██ "),
        TileKind.WUMPUS: ("██ ██", " ███ "),
        TileKind.DEAD_WUMPUS: ("▒▒ ▒▒", " ▒▒▒ "),
        TileKind.PIT: ("░▒▒▒░", "█████"),
        TileKind.BAT: ("█   █", "·███·"),
        TileKind.GOLD: (" ███ ", "  █  "),
        TileKind.EMPTY: ("     ", "  ·· "),
        TileKind.START: ("█   █", " INI "),
        TileKind.EXIT: (" ███ ", " SAI "),
    }
)


# ---------------------------------------------------------------------------
# Effect sprites
#
# Purely ephemeral overlays drawn on top of a tile while an animation plays.
# They depict something the game already reported and are chosen from fixed
# tables, never at random, so they cannot touch the seeded run.
# ---------------------------------------------------------------------------

TRAIL_SPRITE = (
    "          ",
    "   ▒▒▒▒   ",
    "  ▒▒▒▒▒▒  ",
    "   ▒▒▒▒   ",
    "          ",
)

PROJECTILE_SPRITES = (
    (
        "          ",
        "          ",
        "    ██    ",
        "          ",
        "          ",
    ),
    (
        "          ",
        "          ",
        "  ██████  ",
        "          ",
        "          ",
    ),
)

BUMP_SPRITE = (
    "  ██  ██  ",
    "   ████   ",
    "    ██    ",
    "   ████   ",
    "  ██  ██  ",
)

DEATH_SPRITE = (
    " ██    ██ ",
    "  ██  ██  ",
    "   ████   ",
    "  ██  ██  ",
    " ██    ██ ",
)

GOLD_BURST_SPRITES = (
    (
        " *  ██  * ",
        "   ████   ",
        "* ██████ *",
        "   ████   ",
        " *  ██  * ",
    ),
    (
        "  +    +  ",
        "    ██    ",
        "+  ████  +",
        "    ██    ",
        "  +    +  ",
    ),
    (
        "    ·     ",
        "          ",
        "·        ·",
        "          ",
        "     ·    ",
    ),
)

GLITCH_SPRITES = (
    (
        "▒▒  ▒▒  ▒▒",
        "  ▒▒  ▒▒  ",
        "▒▒  ▒▒  ▒▒",
        "  ▒▒  ▒▒  ",
        "▒▒  ▒▒  ▒▒",
    ),
    (
        "  ░░  ░░  ",
        "░░  ░░  ░░",
        "  ░░  ░░  ",
        "░░  ░░  ░░",
        "  ░░  ░░  ",
    ),
)


def tile_lines(
    kind: TileKind, direction: Direction | None = None
) -> tuple[str, ...]:
    """Return the `TILE_HEIGHT` sprite lines, each `TILE_WIDTH` columns wide."""

    if kind is TileKind.AGENT:
        if direction is None:
            raise ValueError("The agent sprite requires a facing direction")
        return _AGENT_SPRITES[direction]
    return _SPRITES[kind]


def tile_style(kind: TileKind) -> str:
    """Return the Rich style that communicates this tile's meaning."""

    return TILE_STYLES[kind]


def legend_icon(kind: TileKind) -> tuple[str, ...]:
    """Return the miniature of a tile's own sprite, for the legend."""

    return _LEGEND_SPRITES[kind]
