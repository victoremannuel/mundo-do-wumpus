"""Renderables for every fixed panel of the retro interface.

Each function turns already-computed presentation state into styled text. They
make no domain decisions, keep no state between calls, and draw only characters
of predictable single-column width so the panels stay aligned.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from rich.text import Text

from wumpus.agent.reasoning import DecisionReason
from wumpus.domain import Direction, Perception, Position
from wumpus.game.config import START_POSITION, GameConfig
from wumpus.game.objective import GameObjective
from wumpus.game.engine import GameOutcome
from wumpus.ui.retro_animation import (
    sensor_is_emphasised,
    sensor_motif,
)
from wumpus.ui.retro_session import MODE_LABELS, GameMode
from wumpus.ui.retro_state import TurnSnapshot
from wumpus.ui.retro_tiles import (
    LEGEND_ICON_HEIGHT,
    LEGEND_ICON_WIDTH,
    TileKind,
    legend_icon,
    tile_style,
)
from wumpus.ui.symbols import (
    RETRO_BANNER_STYLE,
    RETRO_LABEL_STYLE,
    RETRO_OUTCOME_STYLES,
    RETRO_SENSOR_OFF_STYLE,
    RETRO_SENSOR_ON_STYLES,
    RETRO_STATUS_STYLES,
    RETRO_TEXT,
    RETRO_TEXT_DIM,
    RETRO_VALUE_STYLE,
)


TITLE = "M U N D O   D O   W U M P U S"
SUBTITLE = "RETRO CAVE EXPLORATION"

KNOWN_MAP_TITLE = "MAPA CONHECIDO PELO AGENTE"
REAL_MAP_TITLE = "MAPA REAL — DEBUG"

# One control bar per mode: an autonomous run is driven by execution keys, a
# manual run by movement keys, and showing the other mode's keys would only
# invite presses that do nothing.
AUTONOMOUS_CONTROLS = (
    "[P] PAUSE  [N] STEP  [D] DEBUG  [-] SLOWER  [+] FASTER  [R] RESTART  [Q] QUIT"
)
MANUAL_CONTROLS = (
    "[↑] MOVER  [←/→] VIRAR  [G] PEGAR  [F] ATIRAR"
    "  [D] DEBUG  [R] RESTART  [Q] QUIT"
)
CONTROLS = AUTONOMOUS_CONTROLS

MODE_CONTROLS = MappingProxyType(
    {
        GameMode.AUTONOMOUS: AUTONOMOUS_CONTROLS,
        GameMode.MANUAL: MANUAL_CONTROLS,
    }
)

DECISION_TITLES = MappingProxyType(
    {
        GameMode.AUTONOMOUS: "DECISÃO",
        GameMode.MANUAL: "COMANDO",
    }
)

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
    (("INÍCIO", TileKind.START), ("SAÍDA", TileKind.EXIT)),
)
_LEGEND_LABEL_WIDTH = 13
_LEGEND_COLUMN_WIDTH = LEGEND_ICON_WIDTH + 1 + _LEGEND_LABEL_WIDTH
LEGEND_HEIGHT = len(_LEGEND_ROWS) * LEGEND_ICON_HEIGHT


def format_position(position: Position) -> str:
    return f"[{position.row},{position.col}]"


def render_header(banner: str | None = None) -> Text:
    """Build the compact title bar; the board, not the header, is the focus."""

    text = Text(no_wrap=True, overflow="ellipsis", justify="center")
    text.append(TITLE, style=f"bold {RETRO_TEXT}")
    text.append("   ·   ", style=RETRO_TEXT_DIM)
    text.append(banner or SUBTITLE, style=RETRO_BANNER_STYLE if banner else RETRO_TEXT_DIM)
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


def render_sensors(
    perception: Perception,
    sensor_phases: Mapping[str, int] | None = None,
) -> Text:
    """Build the sensor panel as lit and unlit indicators."""

    text = Text(no_wrap=True, overflow="ellipsis")
    phases = sensor_phases or {}
    for index, (label, active) in enumerate(sensor_readings(perception)):
        if index:
            text.append("\n")
        phase = phases.get(label)
        style = RETRO_SENSOR_ON_STYLES[label] if active else RETRO_SENSOR_OFF_STYLE
        label_style = style if active else RETRO_LABEL_STYLE
        if sensor_is_emphasised(phase):
            label_style = f"bold {style}"
        text.append(f"{sensor_motif(label, phase, active=active)} ", style=style)
        text.append(f"{label:<10}", style=label_style)
        text.append("ON " if active else "OFF", style=style)
    return text


def render_agent_status(
    snapshot: TurnSnapshot,
    *,
    turns: int,
    state_label: str,
    speed_label: str,
    seed: int,
    debug_enabled: bool,
    mode: GameMode = GameMode.AUTONOMOUS,
    config: GameConfig | None = None,
    objective: GameObjective = GameObjective.COLLECT_ALL_GOLD,
) -> Text:
    """Build the agent HUD, including execution state the player controls."""

    text = Text(no_wrap=True, overflow="ellipsis")
    game_config = config if config is not None else GameConfig()
    _append_field(text, "POS", format_position(snapshot.position))
    _append_field(text, "DIR", DIRECTION_NAMES[snapshot.direction])
    _append_field(text, "OURO", f"{snapshot.collected_gold} / {game_config.gold_count}")
    _append_field(text, "SCORE", str(snapshot.score))
    _append_field(text, "TURNOS", str(turns))
    _append_field(text, "MODO", MODE_LABELS[mode])
    objective_label = (
        "ESCAPAR RÁPIDO"
        if objective is GameObjective.ESCAPE_FAST
        else "TODOS OS OUROS"
    )
    _append_field(text, "OBJETIVO", objective_label)
    _append_field(text, "SAÍDA", format_position(game_config.exit_position))
    _append_field(
        text,
        "W/P/G/B",
        f"{game_config.wumpus_count} / {game_config.pit_count} / "
        f"{game_config.gold_count} / {game_config.bat_count}",
    )
    text.append("\n")
    _append_field(
        text,
        "ESTADO",
        state_label,
        value_style=RETRO_STATUS_STYLES.get(state_label, RETRO_VALUE_STYLE),
    )
    _append_field(text, "VELOC", speed_label)
    _append_field(text, "SEED", str(seed))
    _append_field(text, "DEBUG", "ON" if debug_enabled else "OFF")
    return text


def render_decision(
    reason: DecisionReason | None, mode: GameMode = GameMode.AUTONOMOUS
) -> Text:
    """Build the reasoning panel from the agent's own structured decision."""

    text = Text(overflow="fold")
    if reason is None:
        text.append("Nenhuma decisão registrada ainda.", style=RETRO_TEXT_DIM)
        return text

    text.append("AÇÃO\n", style=RETRO_LABEL_STYLE)
    action_name = reason.action.name if reason.action is not None else "-"
    text.append(f"{action_name}\n\n", style=RETRO_VALUE_STYLE)
    if mode is GameMode.MANUAL:
        text.append("ORIGEM\n", style=RETRO_LABEL_STYLE)
        text.append("JOGADOR", style=RETRO_VALUE_STYLE)
    else:
        text.append("ALVO\n", style=RETRO_LABEL_STYLE)
        target = "-" if reason.target is None else format_position(reason.target)
        text.append(f"{target}\n\n", style=RETRO_VALUE_STYLE)
        text.append("MOTIVO\n", style=RETRO_LABEL_STYLE)
        text.append(reason.reason, style=RETRO_TEXT)
    return text


def render_legend() -> Text:
    """Build the legend using exactly the styles the board uses."""

    text = Text(no_wrap=True, overflow="ellipsis")
    for row_index, row in enumerate(_LEGEND_ROWS):
        for icon_line in range(LEGEND_ICON_HEIGHT):
            if row_index or icon_line:
                text.append("\n")
            for label, kind in row:
                if label is None or kind is None:
                    text.append(" " * _LEGEND_COLUMN_WIDTH)
                    continue
                text.append(legend_icon(kind)[icon_line], style=tile_style(kind))
                text.append(" ")
                visible_label = label if icon_line == 0 else ""
                text.append(
                    f"{visible_label:<{_LEGEND_LABEL_WIDTH}}",
                    style=RETRO_LABEL_STYLE,
                )
    return text


def render_footer(
    state_label: str,
    speed_label: str,
    mode: GameMode = GameMode.AUTONOMOUS,
) -> Text:
    """Build the always-visible control bar."""

    text = Text(no_wrap=True, overflow="ellipsis")
    text.append(f" {MODE_CONTROLS[mode]}", style=RETRO_TEXT_DIM)
    text.append("   ")
    text.append(state_label, style=RETRO_STATUS_STYLES.get(state_label, RETRO_VALUE_STYLE))
    if mode is GameMode.AUTONOMOUS:
        text.append(f"  {speed_label}", style=RETRO_TEXT_DIM)
    return text


def render_endgame(
    outcome: GameOutcome,
    seed: int,
    *,
    mode: GameMode = GameMode.AUTONOMOUS,
    objective: GameObjective = GameObjective.COLLECT_ALL_GOLD,
    config: GameConfig | None = None,
) -> Text:
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
    _append_field(text, "MODO", MODE_LABELS[mode])
    _append_field(
        text,
        "OBJETIVO",
        "ESCAPAR RÁPIDO" if objective is GameObjective.ESCAPE_FAST else "TODOS OS OUROS",
    )
    _append_field(text, "SCORE", str(outcome.score))
    _append_field(text, "GOLD", str(outcome.collected_gold))
    _append_field(text, "WUMPUS", str(outcome.killed_wumpus))
    _append_field(text, "TURNS", str(outcome.turns))
    _append_field(text, "VISITED", str(outcome.visited_cells))
    _append_field(text, "SEED", "ALEATÓRIA" if seed is None else str(seed))
    game_config = config if config is not None else GameConfig()
    _append_field(text, "INÍCIO", format_position(START_POSITION))
    _append_field(text, "SAÍDA", format_position(game_config.exit_position))
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
