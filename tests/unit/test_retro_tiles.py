"""Tests for the retro pixel-tile engine and its map geometry."""

from __future__ import annotations

import random

import pytest
from rich.cells import cell_len

from wumpus.agent import KnowledgeBase
from wumpus.debug.retro_renderer import build_real_map_view
from wumpus.domain import Direction, EntityType, Position
from wumpus.environment.generator import GeneratedMap
from wumpus.environment.world import World
from wumpus.ui.retro_map import map_board_height, map_board_width, render_map
from wumpus.ui.retro_state import (
    MapView,
    build_known_map_view,
    classify_known_cell,
)
from wumpus.ui.retro_panels import render_legend
from wumpus.ui.retro_tiles import (
    LEGEND_ICON_HEIGHT,
    LEGEND_ICON_WIDTH,
    TILE_HEIGHT,
    TILE_WIDTH,
    TileKind,
    legend_icon,
    tile_lines,
    tile_style,
)


def every_sprite() -> list[tuple[TileKind, Direction | None]]:
    sprites: list[tuple[TileKind, Direction | None]] = []
    for kind in TileKind:
        if kind is TileKind.AGENT:
            sprites.extend((kind, direction) for direction in Direction)
        else:
            sprites.append((kind, None))
    return sprites


def test_every_sprite_is_exactly_five_lines_of_ten_visual_columns() -> None:
    for kind, direction in every_sprite():
        lines = tile_lines(kind, direction)

        assert len(lines) == TILE_HEIGHT, kind
        for line in lines:
            # Visual width, not `len`: a double-width glyph would silently break
            # the whole board even though the string length looked correct.
            assert cell_len(line) == TILE_WIDTH, (kind, direction, line)


def test_every_tile_kind_has_a_style() -> None:
    for kind in TileKind:
        assert tile_style(kind)


def test_legend_uses_distinct_recognizable_mini_sprites() -> None:
    kinds = (
        TileKind.AGENT,
        TileKind.WUMPUS,
        TileKind.PIT,
        TileKind.BAT,
        TileKind.GOLD,
        TileKind.START,
        TileKind.EXIT,
    )
    icons = {kind: legend_icon(kind) for kind in kinds}
    assert len(set(icons.values())) == len(kinds)
    for icon in icons.values():
        assert len(icon) == LEGEND_ICON_HEIGHT
        assert {cell_len(line) for line in icon} == {LEGEND_ICON_WIDTH}
    output = render_legend().plain
    assert all(
        label in output
        for label in ("AGENTE", "WUMPUS", "POÇO", "MORCEGO", "OURO", "INÍCIO", "SAÍDA")
    )
    assert len({legend_icon(kind) for kind in TileKind}) == len(TileKind)


def test_the_agent_has_a_distinct_sprite_for_each_of_the_four_directions() -> None:
    sprites = {direction: tile_lines(TileKind.AGENT, direction) for direction in Direction}

    assert len(set(sprites.values())) == len(Direction)


def test_the_agent_sprite_requires_a_direction() -> None:
    with pytest.raises(ValueError, match="facing direction"):
        tile_lines(TileKind.AGENT)


def test_classification_covers_every_knowledge_state_in_priority_order() -> None:
    knowledge = KnowledgeBase(4, 4)
    unknown = Position(4, 4)
    safe = Position(1, 2)
    visited = Position(1, 1)
    risky = Position(2, 3)
    wumpus = Position(3, 3)
    pit = Position(3, 1)
    bat = Position(4, 2)

    knowledge.mark_safe(safe)
    knowledge.mark_visited(visited)
    knowledge.mark_safe(visited)
    knowledge.mark_possible(risky, EntityType.PIT)
    knowledge.mark_confirmed(wumpus, EntityType.WUMPUS)
    knowledge.mark_confirmed(pit, EntityType.PIT)
    knowledge.mark_confirmed(bat, EntityType.BAT)

    expected = {
        unknown: TileKind.UNKNOWN,
        safe: TileKind.SAFE,
        visited: TileKind.VISITED,
        risky: TileKind.RISK,
        wumpus: TileKind.WUMPUS,
        pit: TileKind.PIT,
        bat: TileKind.BAT,
    }
    for position, kind in expected.items():
        assert classify_known_cell(knowledge.cell(position)) is kind, position


def test_a_dead_wumpus_is_drawn_apart_from_a_live_one() -> None:
    knowledge = KnowledgeBase(3, 3)
    position = Position(3, 3)
    knowledge.mark_confirmed(position, EntityType.WUMPUS)
    knowledge.mark_wumpus_dead(position)

    assert classify_known_cell(knowledge.cell(position)) is TileKind.DEAD_WUMPUS
    assert tile_style(TileKind.DEAD_WUMPUS) != tile_style(TileKind.WUMPUS)


def test_the_agent_is_drawn_on_top_of_whatever_its_room_holds() -> None:
    knowledge = KnowledgeBase(3, 3)
    position = Position(2, 2)
    knowledge.mark_possible(position, EntityType.BAT)
    view = build_known_map_view(knowledge, position, Direction.EAST)

    assert view.kind_at(position) is TileKind.AGENT
    assert view.tiles[position] is TileKind.RISK


def test_an_empty_knowledge_base_reveals_nothing_but_fog_and_the_agent() -> None:
    knowledge = KnowledgeBase(6, 6)
    view = build_known_map_view(knowledge, Position(1, 1), Direction.NORTH)

    kinds = {view.kind_at(position) for position in knowledge.all_cells}

    assert kinds == {TileKind.UNKNOWN, TileKind.AGENT}


def test_the_board_marks_start_and_exit_from_the_very_first_frame() -> None:
    """Both structural rooms are public rules, so fog never hides either one."""

    knowledge = KnowledgeBase(6, 6)
    view = build_known_map_view(knowledge, Position(3, 3), Direction.NORTH)

    assert view.start_position == Position(1, 1)
    assert view.exit_position == Position(6, 6)
    assert view.marker_at(Position(1, 1)) is TileKind.START
    assert view.marker_at(Position(6, 6)) is TileKind.EXIT
    assert view.marker_at(Position(3, 3)) is None

    board = render_map(view).plain
    assert board.count("INI") == 1
    assert board.count("SAI") == 1


@pytest.mark.parametrize(
    ("position", "label", "marker"),
    (
        (Position(1, 1), "INI", TileKind.START),
        (Position(6, 6), "SAI", TileKind.EXIT),
    ),
)
def test_the_agent_never_fully_hides_the_room_it_stands_on(
    position: Position, label: str, marker: TileKind
) -> None:
    knowledge = KnowledgeBase(6, 6)
    occupied = render_map(
        build_known_map_view(knowledge, position, Direction.NORTH)
    ).plain
    elsewhere = render_map(
        build_known_map_view(knowledge, Position(3, 3), Direction.NORTH)
    ).plain

    # The marker survives the agent standing on it...
    assert occupied.count(label) == 1
    # ...and the agent is still painted, so the two boards cannot be identical.
    assert occupied != elsewhere
    assert tile_lines(marker) != tile_lines(TileKind.UNKNOWN)


def test_a_six_by_six_board_has_the_exact_projected_geometry() -> None:
    knowledge = KnowledgeBase(6, 6)
    view = build_known_map_view(knowledge, Position(1, 1), Direction.NORTH)

    lines = render_map(view).plain.split("\n")

    assert map_board_width(6) == 70
    assert map_board_height(6) == 38
    assert len(lines) == map_board_height(6)
    assert {cell_len(line) for line in lines} == {map_board_width(6)}


def test_the_board_labels_rows_from_the_top_and_columns_left_to_right() -> None:
    knowledge = KnowledgeBase(6, 6)
    view = build_known_map_view(knowledge, Position(1, 1), Direction.NORTH)

    lines = render_map(view).plain.split("\n")
    ruler = lines[0]
    row_labels = [line[:3].strip() for line in lines if line[:3].strip()]

    assert ruler.index("1") < ruler.index("6")
    assert row_labels == ["6", "5", "4", "3", "2", "1"]


def test_every_board_row_and_column_gets_one_full_tile() -> None:
    knowledge = KnowledgeBase(6, 6)
    view = build_known_map_view(knowledge, Position(1, 1), Direction.NORTH)

    lines = render_map(view).plain.split("\n")
    rule_lines = [line for line in lines if "─" in line]
    tile_rows = [line for line in lines if "│" in line]

    assert len(rule_lines) == view.rows + 1
    assert len(tile_rows) == view.rows * TILE_HEIGHT
    assert all(line.count("│") == view.cols + 1 for line in tile_rows)


def test_the_debug_adapter_maps_every_real_entity_to_its_own_tile() -> None:
    hidden = {
        Position(3, 1): EntityType.WUMPUS,
        Position(3, 2): EntityType.PIT,
        Position(2, 2): EntityType.GOLD,
        Position(2, 3): EntityType.BAT,
    }
    world = World(GeneratedMap(rows=3, cols=3, entities=hidden), rng=random.Random(7))

    view = build_real_map_view(world.debug_snapshot())

    assert isinstance(view, MapView)
    assert view.tiles[Position(3, 1)] is TileKind.WUMPUS
    assert view.tiles[Position(3, 2)] is TileKind.PIT
    assert view.tiles[Position(2, 2)] is TileKind.GOLD
    assert view.tiles[Position(2, 3)] is TileKind.BAT
    assert view.tiles[Position(1, 3)] is TileKind.EMPTY
    assert view.kind_at(world.agent_position) is TileKind.AGENT


def test_the_real_board_uses_the_same_geometry_as_the_known_board() -> None:
    world = World(GeneratedMap(rows=6, cols=6, entities={}), rng=random.Random(7))

    lines = render_map(build_real_map_view(world.debug_snapshot())).plain.split("\n")

    assert len(lines) == map_board_height(6)
    assert {cell_len(line) for line in lines} == {map_board_width(6)}


def test_the_real_board_marks_the_same_start_and_exit_rooms() -> None:
    """Debug shows the structural rooms too; neither is secret information."""

    world = World(GeneratedMap(rows=6, cols=6, entities={}), rng=random.Random(7))

    view = build_real_map_view(world.debug_snapshot())

    assert view.marker_at(Position(1, 1)) is TileKind.START
    assert view.marker_at(Position(6, 6)) is TileKind.EXIT
    board = render_map(view).plain
    assert board.count("INI") == 1
    assert board.count("SAI") == 1
