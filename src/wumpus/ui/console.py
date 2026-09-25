"""Rich console presentation for the known map, perceptions, and reasoning.

Renders only what the agent already exposes through `AgentObservation`,
`KnowledgeBase`, and `DecisionReason` (sections 62-68). It contains no domain
decisions -- classification and action choice remain the agent's
responsibility; this module only maps that state to text, color, and layout.
"""

from __future__ import annotations

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from wumpus.agent.knowledge import KnowledgeBase
from wumpus.agent.reasoning import DecisionReason
from wumpus.domain import AgentObservation, Direction, Position
from wumpus.game.engine import GameOutcome
from wumpus.ui.symbols import (
    AGENT_COLOR,
    AGENT_SYMBOLS,
    BAT_COLOR,
    BAT_SYMBOL,
    DIRECTION_LABELS,
    GLITTER_COLOR,
    PIT_COLOR,
    PIT_SYMBOL,
    POSSIBLE_DANGER_COLOR,
    RISK_SYMBOL,
    SAFE_COLOR,
    SAFE_SYMBOL,
    UNKNOWN_COLOR,
    UNKNOWN_SYMBOL,
    VISITED_COLOR,
    WUMPUS_COLOR,
    WUMPUS_SYMBOL,
)


def _format_position(position: Position) -> str:
    return f"[{position.row},{position.col}]"


def _cell_text(knowledge: KnowledgeBase, position: Position) -> Text:
    cell = knowledge.cell(position)

    if cell.confirmed_wumpus:
        return Text(f" {WUMPUS_SYMBOL} ", style=WUMPUS_COLOR)
    if cell.confirmed_pit:
        return Text(f" {PIT_SYMBOL} ", style=PIT_COLOR)
    if cell.confirmed_bat:
        return Text(f" {BAT_SYMBOL} ", style=BAT_COLOR)
    if cell.possible_pit or cell.possible_wumpus or cell.possible_bat:
        return Text(f" {RISK_SYMBOL} ", style=POSSIBLE_DANGER_COLOR)
    if cell.visited:
        return Text(f" {SAFE_SYMBOL} ", style=VISITED_COLOR)
    if cell.safe:
        return Text(f" {SAFE_SYMBOL} ", style=SAFE_COLOR)
    return Text(f" {UNKNOWN_SYMBOL} ", style=UNKNOWN_COLOR)


def render_known_map(
    knowledge: KnowledgeBase,
    agent_position: Position,
    agent_direction: Direction,
) -> Panel:
    """Build the known-map panel (section 62), agent row first from the top."""

    table = Table(box=None, show_header=False, padding=(0, 1))
    for _ in range(knowledge.cols):
        table.add_column(justify="center")

    for row in range(knowledge.rows, 0, -1):
        cells = []
        for col in range(1, knowledge.cols + 1):
            position = Position(row, col)
            if position == agent_position:
                cells.append(Text(AGENT_SYMBOLS[agent_direction], style=AGENT_COLOR))
            else:
                cells.append(_cell_text(knowledge, position))
        table.add_row(*cells)

    return Panel(table, title="MAPA CONHECIDO PELO AGENTE", border_style="white")


def render_perceptions(observation: AgentObservation) -> Panel:
    """Build the perceptions panel (section 65)."""

    perception = observation.perception
    labels = (
        ("Fedor", perception.stench, None),
        ("Brisa", perception.breeze, None),
        ("Morcego", perception.bat_noise, None),
        ("Brilho", perception.glitter, GLITTER_COLOR),
        ("Impacto", perception.bump, None),
        ("Grito", perception.scream, None),
    )
    body = Text()
    for label, value, color in labels:
        line = f"{label:<10}: {'SIM' if value else 'NÃO'}\n"
        body.append(line, style=color if value else None)
    return Panel(body, title="PERCEPÇÕES", border_style="white")


def render_agent_status(observation: AgentObservation, steps: int | None = None) -> Panel:
    """Build the agent status panel (section 66)."""

    body = Text()
    body.append(f"Posição        {_format_position(observation.position)}\n")
    body.append(f"Direção        {DIRECTION_LABELS[observation.direction]}\n")
    body.append(f"Ouro           {observation.collected_gold}\n")
    body.append(f"Pontuação      {observation.score}\n")
    if steps is not None:
        body.append(f"Passos         {steps}\n")
    return Panel(body, title="AGENTE", border_style="white")


def render_reasoning(reason: DecisionReason | None) -> Panel:
    """Build the reasoning panel (sections 67-68)."""

    if reason is None:
        body = Text("Nenhuma decisão registrada ainda.")
    else:
        body = Text()
        if reason.target is not None:
            body.append(f"{reason.reason} ({_format_position(reason.target)})\n")
        else:
            body.append(f"{reason.reason}\n")
        action_name = reason.action.name if reason.action is not None else "-"
        body.append(f"Ação: {action_name}")
    return Panel(body, title="DECISÃO DO AGENTE", border_style="white")


class ConsoleRenderer:
    """Render one turn's known state and reasoning using `rich`."""

    def __init__(self, console: Console | None = None) -> None:
        self._console = console if console is not None else Console()

    def render(
        self,
        observation: AgentObservation,
        knowledge: KnowledgeBase,
        reason: DecisionReason | None = None,
        steps: int | None = None,
    ) -> None:
        """Print one turn's panels: known map, perceptions, agent, reasoning."""

        self._console.print(
            Panel(Text("MUNDO DO WUMPUS", justify="center"), border_style="bright_white")
        )
        self._console.print(
            render_known_map(knowledge, observation.position, observation.direction)
        )
        self._console.print(
            Group(
                render_perceptions(observation),
                render_agent_status(observation, steps),
                render_reasoning(reason),
            )
        )

    def render_final(self, outcome: GameOutcome) -> None:
        """Print the final outcome summary."""

        body = Text()
        body.append(f"Resultado       {outcome.status.name}\n")
        body.append(f"Pontuação       {outcome.score}\n")
        body.append(f"Ouro coletado   {outcome.collected_gold}\n")
        body.append(f"Wumpus mortos   {outcome.killed_wumpus}\n")
        body.append(f"Turnos          {outcome.turns}\n")
        body.append(f"Células visitadas {outcome.visited_cells}\n")
        self._console.print(Panel(body, title="RESULTADO FINAL", border_style="bright_white"))
