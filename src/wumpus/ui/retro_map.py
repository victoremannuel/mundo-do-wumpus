"""Draws a `MapView` as a large pixel-art board with discrete coordinates.

The board is the protagonist of the interface, so its size is derived from the
tile geometry instead of from the available space: rooms are never squashed to
make something else fit. Row labels sit in a narrow left gutter and column
labels on a single ruler line above the board, both dim so they never compete
with the tiles themselves.
"""

from __future__ import annotations

from rich.text import Text

from wumpus.domain import Position
from wumpus.ui.retro_state import MapView
from wumpus.ui.retro_tiles import TILE_HEIGHT, TILE_WIDTH, TileKind, tile_lines, tile_style
from wumpus.ui.symbols import RETRO_BORDER_STYLE, RETRO_COORD_STYLE


MAP_GUTTER_WIDTH = 3
MAP_RULER_HEIGHT = 1
_LABEL_LINE_INDEX = TILE_HEIGHT // 2


def map_board_width(cols: int) -> int:
    """Terminal columns one rendered board occupies, gutter and borders included."""

    return MAP_GUTTER_WIDTH + cols * (TILE_WIDTH + 1) + 1


def map_board_height(rows: int) -> int:
    """Terminal lines one rendered board occupies, ruler and borders included."""

    return MAP_RULER_HEIGHT + 1 + rows * (TILE_HEIGHT + 1)


def render_map(view: MapView) -> Text:
    """Render the whole board as one styled, non-wrapping block of text."""

    text = Text(no_wrap=True, overflow="ignore")
    text.append(_ruler(view.cols), style=RETRO_COORD_STYLE)
    text.append("\n")
    text.append(_rule_line(view.cols, "┌", "┬", "┐"), style=RETRO_BORDER_STYLE)

    for index, row in enumerate(range(view.rows, 0, -1)):
        text.append("\n")
        _append_room_row(text, view, row)
        text.append("\n")
        corners = ("└", "┴", "┘") if index == view.rows - 1 else ("├", "┼", "┤")
        text.append(_rule_line(view.cols, *corners), style=RETRO_BORDER_STYLE)

    return text


def _ruler(cols: int) -> str:
    parts = [" " * MAP_GUTTER_WIDTH]
    for col in range(1, cols + 1):
        parts.append(" ")
        parts.append(f"{col:^{TILE_WIDTH}}")
    parts.append(" ")
    return "".join(parts)


def _rule_line(cols: int, left: str, middle: str, right: str) -> str:
    segment = "─" * TILE_WIDTH
    return (
        " " * MAP_GUTTER_WIDTH
        + left
        + middle.join(segment for _ in range(cols))
        + right
    )


def _append_room_row(text: Text, view: MapView, row: int) -> None:
    kinds: list[TileKind] = []
    sprites: list[tuple[str, ...]] = []
    for col in range(1, view.cols + 1):
        kind = view.kind_at(Position(row, col))
        kinds.append(kind)
        sprites.append(tile_lines(kind, view.agent_direction))

    for line_index in range(TILE_HEIGHT):
        if line_index:
            text.append("\n")
        label = (
            f"{row:^{MAP_GUTTER_WIDTH}}"
            if line_index == _LABEL_LINE_INDEX
            else " " * MAP_GUTTER_WIDTH
        )
        text.append(label, style=RETRO_COORD_STYLE)
        for column_index, kind in enumerate(kinds):
            text.append("│", style=RETRO_BORDER_STYLE)
            text.append(sprites[column_index][line_index], style=tile_style(kind))
        text.append("│", style=RETRO_BORDER_STYLE)
