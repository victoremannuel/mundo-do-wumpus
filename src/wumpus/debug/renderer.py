"""Professor-mode renderer with explicit access to the real world map."""

from __future__ import annotations

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from wumpus.agent.knowledge import KnowledgeBase
from wumpus.agent.reasoning import DecisionReason
from wumpus.domain import AgentObservation, EntityType, Position
from wumpus.environment.world import DebugWorldSnapshot, World
from wumpus.ui.console import (
    render_agent_status,
    render_known_map,
    render_perceptions,
    render_reasoning,
)
from wumpus.ui.symbols import (
    AGENT_COLOR,
    AGENT_SYMBOLS,
    BAT_COLOR,
    BAT_SYMBOL,
    EMPTY_SYMBOL,
    GOLD_COLOR,
    GOLD_SYMBOL,
    PIT_COLOR,
    PIT_SYMBOL,
    UNKNOWN_COLOR,
    WUMPUS_COLOR,
    WUMPUS_SYMBOL,
)


_ENTITY_PRESENTATION = {
    EntityType.EMPTY: (EMPTY_SYMBOL, UNKNOWN_COLOR),
    EntityType.WUMPUS: (WUMPUS_SYMBOL, WUMPUS_COLOR),
    EntityType.PIT: (PIT_SYMBOL, PIT_COLOR),
    EntityType.GOLD: (GOLD_SYMBOL, GOLD_COLOR),
    EntityType.BAT: (BAT_SYMBOL, BAT_COLOR),
}


def render_real_map(snapshot: DebugWorldSnapshot) -> Panel:
    """Build the real-map panel from an explicit immutable debug snapshot."""

    table = Table(box=None, show_header=False, padding=(0, 1))
    for _ in range(snapshot.cols):
        table.add_column(justify="center")

    for row in range(snapshot.rows, 0, -1):
        cells = []
        for col in range(1, snapshot.cols + 1):
            position = Position(row, col)
            if position == snapshot.agent_position:
                cells.append(
                    Text(AGENT_SYMBOLS[snapshot.agent_direction], style=AGENT_COLOR)
                )
                continue
            symbol, color = _ENTITY_PRESENTATION[snapshot.entity_at(position)]
            cells.append(Text(f" {symbol} ", style=color))
        table.add_row(*cells)

    return Panel(table, title="MAPA REAL", border_style="bright_white")


class DebugRenderer:
    """Render agent knowledge beside hidden state without exposing it to the agent."""

    def __init__(self, console: Console | None = None) -> None:
        self._console = console if console is not None else Console()

    def render(
        self,
        world: World,
        observation: AgentObservation,
        knowledge: KnowledgeBase,
        reason: DecisionReason | None = None,
        steps: int | None = None,
    ) -> None:
        """Print known and real maps plus the ordinary agent-facing panels."""

        snapshot = world.debug_snapshot()
        self._console.print(
            Panel(Text("MUNDO DO WUMPUS", justify="center"), border_style="bright_white")
        )
        self._console.print(
            render_known_map(knowledge, observation.position, observation.direction)
        )
        self._console.print(render_real_map(snapshot))
        self._console.print(
            Group(
                render_perceptions(observation),
                render_agent_status(observation, steps),
                render_reasoning(reason),
            )
        )
