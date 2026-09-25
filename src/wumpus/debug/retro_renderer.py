"""Authorized debug adapter between the real world and the retro interface.

This is the only place that is allowed to read hidden state for the retro
screen. It converts an explicit `DebugWorldSnapshot` into an inert `MapView` --
plain tile kinds and coordinates -- so `wumpus.ui` can draw the real map without
ever importing the environment, the generated map, or the snapshot type. The
conversion is one-way: nothing flows back to the agent, so professor mode stays
pure observation and can never influence a decision.
"""

from __future__ import annotations

from types import MappingProxyType

from wumpus.domain import EntityType, Position
from wumpus.environment.world import DebugWorldSnapshot
from wumpus.ui.retro_state import MapView
from wumpus.ui.retro_tiles import TileKind
from wumpus.game.config import START_POSITION, exit_position_for


_ENTITY_TILES = MappingProxyType(
    {
        EntityType.EMPTY: TileKind.EMPTY,
        EntityType.WUMPUS: TileKind.WUMPUS,
        EntityType.PIT: TileKind.PIT,
        EntityType.GOLD: TileKind.GOLD,
        EntityType.BAT: TileKind.BAT,
    }
)


def build_real_map_view(snapshot: DebugWorldSnapshot) -> MapView:
    """Build the real-map view from an explicit immutable debug snapshot."""

    tiles = {
        Position(row, col): _ENTITY_TILES[snapshot.entity_at(Position(row, col))]
        for row in range(1, snapshot.rows + 1)
        for col in range(1, snapshot.cols + 1)
    }
    return MapView(
        rows=snapshot.rows,
        cols=snapshot.cols,
        tiles=tiles,
        agent_position=snapshot.agent_position,
        agent_direction=snapshot.agent_direction,
        start_position=START_POSITION,
        exit_position=exit_position_for(snapshot.rows, snapshot.cols),
    )
