"""Presentation state for the retro interface.

This module is the boundary. It converts information the agent legitimately
owns -- `AgentObservation`, `ActionResult`, `KnowledgeBase`, `DecisionReason` --
into inert view models the widgets can draw. It never sees `World`, a generated
map, or any hidden entity, and it holds no second authoritative copy of the
game: every value here is either handed in by the engine or derived from it.

The same `MapView` shape is reused by the authorized debug path, which builds it
outside this package from an explicit debug snapshot. That keeps hidden state
out of `wumpus.ui` while still allowing one tile renderer for both maps.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from wumpus.agent.knowledge import KnowledgeBase, KnownCell
from wumpus.agent.reasoning import DecisionReason
from wumpus.domain import ActionResult, AgentObservation, Direction, Perception, Position
from wumpus.ui.retro_tiles import TileKind


# Timer intervals the interface may run at, slowest first. The default must stay
# equal to the CLI's documented `DEFAULT_DELAY`.
SPEED_INTERVALS: tuple[float, ...] = (2.0, 1.0, 0.5, 0.25, 0.1, 0.05)
DEFAULT_INTERVAL = 0.5
DEFAULT_SPEED_INDEX = SPEED_INTERVALS.index(DEFAULT_INTERVAL)
# `--no-delay` uses the fastest interval rather than zero: a zero-length timer
# would starve the event loop and stop the keyboard from responding.
MIN_INTERVAL = SPEED_INTERVALS[-1]
MAX_SPEED_INDEX = len(SPEED_INTERVALS) - 1


class AgentPresentationSource(Protocol):
    """The agent-owned surface the interface is allowed to read."""

    @property
    def memory(self) -> KnowledgeSource: ...

    @property
    def last_reason(self) -> DecisionReason | None: ...

    @property
    def actions_taken(self) -> int: ...


class KnowledgeSource(Protocol):
    """Indirection matching `AgentMemory`, which owns the logical map."""

    @property
    def knowledge(self) -> KnowledgeBase: ...


@dataclass(frozen=True)
class MapView:
    """An inert, fully classified map ready to be drawn as pixel tiles."""

    rows: int
    cols: int
    tiles: Mapping[Position, TileKind]
    agent_position: Position
    agent_direction: Direction

    def kind_at(self, position: Position) -> TileKind:
        """Return the tile for a position, with the agent always on top."""

        if position == self.agent_position:
            return TileKind.AGENT
        return self.tiles.get(position, TileKind.UNKNOWN)


@dataclass(frozen=True)
class TurnSnapshot:
    """The agent-visible state the HUD shows for the current frame."""

    position: Position
    direction: Direction
    perception: Perception
    score: int
    collected_gold: int


def classify_known_cell(cell: KnownCell) -> TileKind:
    """Map one logical classification to a tile, highest priority first.

    The order is confirmed danger, then possible danger, then visited, then
    known-safe, then unknown. Nothing the agent has not inferred can appear, so
    the interface never improves the agent's knowledge.
    """

    if cell.dead_wumpus:
        return TileKind.DEAD_WUMPUS
    if cell.confirmed_wumpus:
        return TileKind.WUMPUS
    if cell.confirmed_pit:
        return TileKind.PIT
    if cell.confirmed_bat:
        return TileKind.BAT
    if cell.possible_pit or cell.possible_wumpus or cell.possible_bat:
        return TileKind.RISK
    if cell.visited:
        return TileKind.VISITED
    if cell.safe:
        return TileKind.SAFE
    return TileKind.UNKNOWN


def build_known_map_view(
    knowledge: KnowledgeBase,
    agent_position: Position,
    agent_direction: Direction,
) -> MapView:
    """Build the map the agent itself believes in, and nothing more."""

    tiles = {
        position: classify_known_cell(knowledge.cell(position))
        for position in knowledge.all_cells
    }
    return MapView(
        rows=knowledge.rows,
        cols=knowledge.cols,
        tiles=tiles,
        agent_position=agent_position,
        agent_direction=agent_direction,
    )


def initial_snapshot(observation: AgentObservation) -> TurnSnapshot:
    """Build the frame shown before the first turn runs."""

    return TurnSnapshot(
        position=observation.position,
        direction=observation.direction,
        perception=observation.perception,
        score=observation.score,
        collected_gold=observation.collected_gold,
    )


def snapshot_after(previous: TurnSnapshot, result: ActionResult) -> TurnSnapshot:
    """Build the frame for the state the environment reports after one action.

    Position, orientation, perception, and score come straight from the
    environment's `ActionResult`. The gold counter is advanced from the same
    `gold_collected` flag the environment itself uses, so the HUD stays exact
    without keeping an independent tally of game state.
    """

    return TurnSnapshot(
        position=result.position,
        direction=result.direction,
        perception=result.perception,
        score=result.total_score,
        collected_gold=previous.collected_gold + (1 if result.gold_collected else 0),
    )
