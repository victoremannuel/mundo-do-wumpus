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
from wumpus.ui.retro_state import MapOverlay, MapView
from wumpus.ui.retro_tiles import (
    TILE_HEIGHT,
    TILE_WIDTH,
    TRAIL_SPRITE,
    TileKind,
    tile_lines,
    tile_style,
)
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


def render_map(view: MapView, overlay: MapOverlay | None = None) -> Text:
    """Render the whole board as one styled, non-wrapping block of text.

    The optional overlay decorates single rooms for the duration of one animation
    frame. It never changes the board's geometry, and once it is gone every room
    is drawn from the `MapView` alone again.
    """

    text = Text(no_wrap=True, overflow="ignore")
    text.append(_ruler(view.cols), style=RETRO_COORD_STYLE)
    text.append("\n")
    text.append(_rule_line(view.cols, "┌", "┬", "┐"), style=RETRO_BORDER_STYLE)

    for index, row in enumerate(range(view.rows, 0, -1)):
        text.append("\n")
        _append_room_row(text, view, row, overlay)
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


def _append_room_row(
    text: Text, view: MapView, row: int, overlay: MapOverlay | None = None
) -> None:
    styles: list[str] = []
    sprites: list[tuple[str, ...]] = []
    for col in range(1, view.cols + 1):
        sprite, style = _room_art(view, Position(row, col), overlay)
        sprites.append(sprite)
        styles.append(style)

    for line_index in range(TILE_HEIGHT):
        if line_index:
            text.append("\n")
        label = (
            f"{row:^{MAP_GUTTER_WIDTH}}"
            if line_index == _LABEL_LINE_INDEX
            else " " * MAP_GUTTER_WIDTH
        )
        text.append(label, style=RETRO_COORD_STYLE)
        for column_index, style in enumerate(styles):
            text.append("│", style=RETRO_BORDER_STYLE)
            text.append(sprites[column_index][line_index], style=style)
        text.append("│", style=RETRO_BORDER_STYLE)


def _room_art(
    view: MapView, position: Position, overlay: MapOverlay | None
) -> tuple[tuple[str, ...], str]:
    """Pick the sprite and style for one room, effects last and on top.

    Order matters: the authoritative tile is resolved first, then an animation may
    paint over it. Because the overlay is discarded when the animation ends, the
    room always falls back to exactly what the knowledge base says.
    """

    kind = view.kind_at(position)
    is_agent = position == view.agent_position

    if overlay is not None and is_agent and overlay.agent_hidden:
        kind = view.tiles.get(position, TileKind.UNKNOWN)
        is_agent = False

    marker = view.marker_at(position)
    base_kind = marker or (view.tiles.get(position, TileKind.UNKNOWN))
    sprite = tile_lines(base_kind)
    style = tile_style(base_kind)
    if is_agent:
        sprite = _composite_sprite(sprite, tile_lines(TileKind.AGENT, view.agent_direction))
        style = tile_style(TileKind.AGENT)

    if overlay is None:
        return sprite, style

    if position in overlay.trail:
        return TRAIL_SPRITE, overlay.trail_style or style
    if position == overlay.projectile:
        return (
            overlay.projectile_sprite or sprite,
            overlay.projectile_style or style,
        )

    flashes = overlay.flashes
    if position in flashes:
        style = flashes[position]
        if overlay.cell_flash_sprite is not None:
            sprite = overlay.cell_flash_sprite

    # A hidden agent's room can still carry an effect sprite -- that is how a
    # teleport shows glitch blocks where the agent is not drawn.
    if position == view.agent_position and overlay.agent_sprite is not None:
        sprite = overlay.agent_sprite
        style = overlay.agent_style or style
    elif is_agent and overlay.agent_style is not None:
        style = overlay.agent_style

    return sprite, style


def _composite_sprite(
    base: tuple[str, ...], overlay: tuple[str, ...]
) -> tuple[str, ...]:
    """Paint non-space agent pixels while retaining START/EXIT marker pixels."""

    return tuple(
        "".join(top if top != " " else bottom for bottom, top in zip(base_line, overlay_line))
        for base_line, overlay_line in zip(base, overlay)
    )
