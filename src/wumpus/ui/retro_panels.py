"""Renderables for every fixed panel of the retro interface.

Each function turns already-computed presentation state into styled text. They
make no domain decisions, keep no state between calls, and draw only characters
of predictable single-column width so the panels stay aligned.
"""

from __future__ import annotations

from types import MappingProxyType

from rich.text import Text

from wumpus.agent.reasoning import DecisionReason
from wumpus.domain import Direction, Perception, Position
from wumpus.game.engine import GameOutcome
from wumpus.ui.retro_state import TurnSnapshot
from wumpus.ui.retro_tiles import TileKind, tile_style
from wumpus.ui.symbols import (
    RETRO_LABEL_STYLE,
    RETRO_OUTCOME_STYLES,
    RETRO_SENSOR_INDICATOR,
    RETRO_SENSOR_OFF_STYLE,
    RETRO_SENSOR_ON_STYLES,
    RETRO_STATUS_STYLES,
    RETRO_TEXT,
    RETRO_TEXT_DIM,
    RETRO_VALUE_STYLE,
)


TITLE = "M U N D O   D O   W U M P U S"
SUBTITLE = "LOGICAL AUTONOMOUS AGENT"

KNOWN_MAP_TITLE = "MAPA CONHECIDO PELO AGENTE"
REAL_MAP_TITLE = "MAPA REAL — DEBUG"

CONTROLS = "[P] PAUSE   [N] STEP   [D] DEBUG   [-] SLOWER   [+] FASTER   [Q] QUIT"

_LABEL_WIDTH = 10

DIRECTION_NAMES = MappingProxyType(
    {
        Direction.NORTH: "NORTE",
        Direction.EAST: "LESTE",
        Direction.SOUTH: "SUL",
        Direction.WEST: "OESTE",
    }
)

SENSOR_LABELS = ("FEDOR", "BRISA", "MORCEGO", "BRILHO", "IMPACTO", "GRITO")

_LEGEND_ROWS = (
    (("AGENTE", TileKind.AGENT), ("RISCO", TileKind.RISK)),
    (("SEGURO", TileKind.SAFE), ("WUMPUS", TileKind.WUMPUS)),
    (("VISITADO", TileKind.VISITED), ("POÇO", TileKind.PIT)),
    (("DESCONHECIDO", TileKind.UNKNOWN), ("MORCEGO", TileKind.BAT)),
    ((None, None), ("OURO", TileKind.GOLD)),
)
_LEGEND_COLUMN_WIDTH = 20


def format_position(position: Position) -> str:
    return f"[{position.row},{position.col}]"


def render_header() -> Text:
    """Build the compact title bar; the board, not the header, is the focus."""

    text = Text(no_wrap=True, overflow="ellipsis", justify="center")
    text.append(TITLE, style=f"bold {RETRO_TEXT}")
    text.append("   ·   ", style=RETRO_TEXT_DIM)
    text.append(SUBTITLE, style=RETRO_TEXT_DIM)
    return text


def sensor_readings(perception: Perception) -> tuple[tuple[str, bool], ...]:
    """Pair each sensor label with its current value, in a stable order."""

    values = (
        perception.stench,
        perception.breeze,
        perception.bat_noise,
        perception.glitter,
        perception.bump,
        perception.scream,
    )
    return tuple(zip(SENSOR_LABELS, values))


def render_sensors(perception: Perception) -> Text:
    """Build the sensor panel as lit and unlit indicators."""

    text = Text(no_wrap=True, overflow="ellipsis")
    for index, (label, active) in enumerate(sensor_readings(perception)):
        if index:
            text.append("\n")
        style = RETRO_SENSOR_ON_STYLES[label] if active else RETRO_SENSOR_OFF_STYLE
        text.append(f"{RETRO_SENSOR_INDICATOR} ", style=style)
        text.append(f"{label:<12}", style=style if active else RETRO_LABEL_STYLE)
        text.append("ON " if active else "OFF", style=style)
    return text


def render_agent_status(
    snapshot: TurnSnapshot,
    *,
    turns: int,
    state_label: str,
    speed_label: str,
    seed: int | None,
    debug_enabled: bool,
) -> Text:
    """Build the agent HUD, including execution state the player controls."""

    text = Text(no_wrap=True, overflow="ellipsis")
    _append_field(text, "POS", format_position(snapshot.position))
    _append_field(text, "DIR", DIRECTION_NAMES[snapshot.direction])
    _append_field(text, "OURO", str(snapshot.collected_gold))
    _append_field(text, "SCORE", str(snapshot.score))
    _append_field(text, "TURNOS", str(turns))
    text.append("\n")
    _append_field(
        text,
        "ESTADO",
        state_label,
        value_style=RETRO_STATUS_STYLES.get(state_label, RETRO_VALUE_STYLE),
    )
    _append_field(text, "VELOC", speed_label)
    _append_field(text, "SEED", "ALEATÓRIA" if seed is None else str(seed))
    _append_field(text, "DEBUG", "ON" if debug_enabled else "OFF")
    return text


def render_decision(reason: DecisionReason | None) -> Text:
    """Build the reasoning panel from the agent's own structured decision."""

    text = Text(overflow="fold")
    if reason is None:
        text.append("Nenhuma decisão registrada ainda.", style=RETRO_TEXT_DIM)
        return text

    text.append("AÇÃO\n", style=RETRO_LABEL_STYLE)
    action_name = reason.action.name if reason.action is not None else "-"
    text.append(f"{action_name}\n\n", style=RETRO_VALUE_STYLE)
    text.append("ALVO\n", style=RETRO_LABEL_STYLE)
    target = "-" if reason.target is None else format_position(reason.target)
    text.append(f"{target}\n\n", style=RETRO_VALUE_STYLE)
    text.append("MOTIVO\n", style=RETRO_LABEL_STYLE)
    text.append(reason.reason, style=RETRO_TEXT)
    return text


def render_legend() -> Text:
    """Build the legend using exactly the styles the board uses."""

    text = Text(no_wrap=True, overflow="ellipsis")
    for index, row in enumerate(_LEGEND_ROWS):
        if index:
            text.append("\n")
        for label, kind in row:
            if label is None or kind is None:
                text.append(" " * _LEGEND_COLUMN_WIDTH)
                continue
            text.append("█ ", style=tile_style(kind))
            text.append(f"{label:<{_LEGEND_COLUMN_WIDTH - 2}}", style=RETRO_LABEL_STYLE)
    return text


def render_footer(state_label: str, speed_label: str) -> Text:
    """Build the always-visible control bar."""

    text = Text(no_wrap=True, overflow="ellipsis")
    text.append(f" {CONTROLS}", style=RETRO_TEXT_DIM)
    text.append("   ")
    text.append(state_label, style=RETRO_STATUS_STYLES.get(state_label, RETRO_VALUE_STYLE))
    text.append(f"  {speed_label}", style=RETRO_TEXT_DIM)
    return text


def render_endgame(outcome: GameOutcome, seed: int | None) -> Text:
    """Build the final summary shown once the engine reports the game is over."""

    status = outcome.status.name
    text = Text(no_wrap=True, overflow="ellipsis", justify="left")
    text.append("GAME OVER\n\n", style=RETRO_OUTCOME_STYLES.get(status, RETRO_VALUE_STYLE))
    _append_field(
        text,
        "RESULT",
        status,
        value_style=RETRO_OUTCOME_STYLES.get(status, RETRO_VALUE_STYLE),
    )
    _append_field(text, "SCORE", str(outcome.score))
    _append_field(text, "GOLD", str(outcome.collected_gold))
    _append_field(text, "WUMPUS", str(outcome.killed_wumpus))
    _append_field(text, "TURNS", str(outcome.turns))
    _append_field(text, "VISITED", str(outcome.visited_cells))
    _append_field(text, "SEED", "ALEATÓRIA" if seed is None else str(seed))
    text.append("\n[Q] EXIT", style=RETRO_TEXT_DIM)
    return text


def render_failure(message: str) -> Text:
    """Build the panel shown when an unexpected interface error stops the run."""

    text = Text(overflow="fold")
    text.append("ERRO INESPERADO\n\n", style=RETRO_STATUS_STYLES["ERROR"])
    text.append(message, style=RETRO_TEXT)
    text.append(
        "\n\nA execução automática foi interrompida. O traceback completo foi"
        " registrado no log da aplicação.\n\n",
        style=RETRO_TEXT_DIM,
    )
    text.append("[Q] EXIT", style=RETRO_TEXT_DIM)
    return text


def render_too_small(width: int, height: int, min_width: int, min_height: int) -> Text:
    """Build the graceful fallback for terminals smaller than the layout."""

    text = Text(justify="center", overflow="fold")
    text.append("TERMINAL MUITO PEQUENO\n\n", style=RETRO_STATUS_STYLES["ERROR"])
    text.append("Tamanho atual\n", style=RETRO_LABEL_STYLE)
    text.append(f"{width} × {height}\n\n", style=RETRO_VALUE_STYLE)
    text.append("Tamanho mínimo recomendado\n", style=RETRO_LABEL_STYLE)
    text.append(f"{min_width} × {min_height}\n\n", style=RETRO_VALUE_STYLE)
    text.append(
        "Aumente a janela do terminal ou reduza o tamanho da fonte.\n\n",
        style=RETRO_TEXT,
    )
    text.append("[Q] Sair", style=RETRO_TEXT_DIM)
    return text


def _append_field(
    text: Text, label: str, value: str, *, value_style: str = RETRO_VALUE_STYLE
) -> None:
    text.append(f"{label:<{_LABEL_WIDTH}}", style=RETRO_LABEL_STYLE)
    text.append(f"{value}\n", style=value_style)
