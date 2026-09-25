"""Persistent retro Textual interface for the autonomous Wumpus agent.

Why Textual drives `GameEngine.step()`
--------------------------------------
The engine owns the whole perceive -> decide -> act -> learn cycle. This app
never reimplements it: a Textual timer (and the manual STEP key) simply asks the
engine to advance exactly one turn, then repaints the persistent widgets. The
widget tree is mounted once and only updated afterwards, so the terminal shows a
single fixed screen instead of a new frame printed under the previous one.

Where the boundary lies
-----------------------
The app is given the agent's own presentation surface (`KnowledgeBase`,
`DecisionReason`, action count) plus the `AgentObservation` and `ActionResult`
values the environment already publishes. It never receives the world, a
generated map, or any hidden entity, and it never imports `wumpus.environment`
or `wumpus.debug`. The real map reaches the screen only as an inert `MapView`
produced by the authorized debug path and injected by the composition root.

No visual randomness
--------------------
Nothing here draws from a random source. The interface therefore cannot consume
the game's seeded RNG, and a fixed seed keeps producing the same game whatever
the player does with pause, speed, or debug.
"""

from __future__ import annotations

import traceback
from collections.abc import Callable

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static

from wumpus.domain import AgentObservation
from wumpus.game.engine import GameEngine, GameOutcome
from wumpus.ui.retro_map import map_board_height, map_board_width, render_map
from wumpus.ui.retro_panels import (
    KNOWN_MAP_TITLE,
    REAL_MAP_TITLE,
    render_agent_status,
    render_decision,
    render_endgame,
    render_failure,
    render_footer,
    render_header,
    render_legend,
    render_sensors,
    render_too_small,
)
from wumpus.ui.retro_state import (
    DEFAULT_SPEED_INDEX,
    MAX_SPEED_INDEX,
    SPEED_INTERVALS,
    AgentPresentationSource,
    MapView,
    TurnSnapshot,
    build_known_map_view,
    initial_snapshot,
    snapshot_after,
)
from wumpus.ui.symbols import (
    RETRO_BACKGROUND,
    RETRO_BORDER,
    RETRO_DEBUG,
    RETRO_PANEL_BACKGROUND,
    RETRO_TEXT,
    RETRO_TEXT_DIM,
)


_DEFAULT_ROWS = 6
_DEFAULT_COLS = 6

HEADER_HEIGHT = 3
FOOTER_HEIGHT = 1
SIDEBAR_WIDTH = 46
_BORDER_THICKNESS = 2

MAP_PANEL_WIDTH = map_board_width(_DEFAULT_COLS) + _BORDER_THICKNESS
MAP_PANEL_HEIGHT = map_board_height(_DEFAULT_ROWS) + _BORDER_THICKNESS

MIN_WIDTH = MAP_PANEL_WIDTH + SIDEBAR_WIDTH
MIN_HEIGHT = HEADER_HEIGHT + MAP_PANEL_HEIGHT + FOOTER_HEIGHT

# Showing both boards at full tile scale needs room for two panels; the HUD is
# kept as well whenever it also fits, and dropped only in the narrow band where
# the alternative would be squashing the tiles.
DUAL_MAP_MIN_WIDTH = 176
DUAL_MAP_WITH_SIDEBAR_MIN_WIDTH = 2 * MAP_PANEL_WIDTH + SIDEBAR_WIDTH

STATE_RUNNING = "RUNNING"
STATE_PAUSED = "PAUSED"
STATE_FINISHED = "FINISHED"
STATE_ERROR = "ERROR"

DebugMapSource = Callable[[], MapView]


class RetroHeader(Static):
    """Compact title bar."""


class PixelMapWidget(Static):
    """One persistent pixel-art board."""


class AgentStatusWidget(Static):
    """Agent HUD."""


class PerceptionWidget(Static):
    """Sensor indicators."""


class DecisionWidget(Static):
    """Structured reasoning panel."""


class LegendWidget(Static):
    """Tile legend."""


class RetroFooter(Static):
    """Always-visible control bar."""


class EndGameOverlay(Static):
    """Final summary shown once the engine reports the game is over."""


class TooSmallNotice(Static):
    """Graceful fallback for terminals smaller than the fixed layout."""


class RetroGameApp(App[GameOutcome | None]):
    """Drive one already-assembled game through a fixed, interactive screen."""

    CSS = f"""
    Screen {{
        layers: base overlay;
        background: {RETRO_BACKGROUND};
        color: {RETRO_TEXT};
        layout: vertical;
        overflow: hidden;
    }}

    #header {{
        height: {HEADER_HEIGHT};
        border: round {RETRO_BORDER};
        background: {RETRO_PANEL_BACKGROUND};
        content-align: center middle;
    }}

    #game-area {{
        height: 1fr;
        layout: horizontal;
        align: center top;
        overflow: hidden;
    }}

    #map-known, #map-real {{
        width: {MAP_PANEL_WIDTH};
        height: {MAP_PANEL_HEIGHT};
        border: round {RETRO_BORDER};
        background: {RETRO_BACKGROUND};
        overflow: hidden;
    }}

    #map-real {{
        border: round {RETRO_DEBUG};
        display: none;
    }}

    #sidebar {{
        width: {SIDEBAR_WIDTH};
        height: {MAP_PANEL_HEIGHT};
        layout: vertical;
        overflow: hidden;
    }}

    #sidebar Static {{
        border: round {RETRO_BORDER};
        background: {RETRO_PANEL_BACKGROUND};
        padding: 0 1;
        overflow: hidden;
    }}

    #status {{ height: 12; }}
    #sensors {{ height: 8; }}
    #decision {{ height: 1fr; }}
    #legend {{ height: 7; }}

    #endgame {{
        height: 1fr;
        border: double {RETRO_BORDER};
        display: none;
    }}

    #footer {{
        height: {FOOTER_HEIGHT};
        background: {RETRO_PANEL_BACKGROUND};
        color: {RETRO_TEXT_DIM};
    }}

    #overlay-too-small {{
        layer: overlay;
        width: 100%;
        height: 100%;
        align: center middle;
        background: {RETRO_BACKGROUND};
        display: none;
    }}

    #too-small {{
        width: 44;
        height: auto;
        border: round {RETRO_BORDER};
        background: {RETRO_PANEL_BACKGROUND};
        padding: 1 2;
    }}
    """

    BINDINGS = [
        ("p", "toggle_pause", "PAUSE"),
        ("space", "toggle_pause", "PAUSE"),
        ("n", "single_step", "STEP"),
        ("d", "toggle_debug", "DEBUG"),
        ("plus", "faster", "FASTER"),
        ("equals_sign", "faster", "FASTER"),
        ("minus", "slower", "SLOWER"),
        ("underscore", "slower", "SLOWER"),
        ("q", "quit_game", "QUIT"),
    ]

    def __init__(
        self,
        *,
        engine: GameEngine,
        agent: AgentPresentationSource,
        initial_observation: AgentObservation,
        seed: int | None = None,
        speed_index: int = DEFAULT_SPEED_INDEX,
        start_paused: bool = False,
        debug_enabled: bool = False,
        debug_map_source: DebugMapSource | None = None,
    ) -> None:
        super().__init__()
        self._engine = engine
        self._agent = agent
        self._seed = seed
        self._snapshot: TurnSnapshot = initial_snapshot(initial_observation)
        self._speed_index = max(0, min(MAX_SPEED_INDEX, speed_index))
        self._paused = start_paused
        self._debug_enabled = debug_enabled and debug_map_source is not None
        self._debug_map_source = debug_map_source
        self._finished = False
        self._outcome: GameOutcome | None = None
        self._step_in_progress = False
        self._failure: str | None = None
        self._timer = None

    # ------------------------------------------------------------------
    # Presentation state
    # ------------------------------------------------------------------

    @property
    def interval(self) -> float:
        """Seconds between automatic turns; never zero, so input stays alive."""

        return SPEED_INTERVALS[self._speed_index]

    @property
    def speed_index(self) -> int:
        return self._speed_index

    @property
    def speed_label(self) -> str:
        return f"{self.interval:.2f}s"

    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def finished(self) -> bool:
        return self._finished

    @property
    def debug_enabled(self) -> bool:
        return self._debug_enabled

    @property
    def outcome(self) -> GameOutcome | None:
        return self._outcome

    @property
    def failure(self) -> str | None:
        """Traceback of an unexpected interface error, kept for diagnosis."""

        return self._failure

    @property
    def state_label(self) -> str:
        if self._failure is not None:
            return STATE_ERROR
        if self._finished:
            return STATE_FINISHED
        return STATE_PAUSED if self._paused else STATE_RUNNING

    # ------------------------------------------------------------------
    # Composition -- the widget tree is built exactly once
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield RetroHeader(render_header(), id="header")
        with Horizontal(id="game-area"):
            yield PixelMapWidget(id="map-known")
            yield PixelMapWidget(id="map-real")
            with Vertical(id="sidebar"):
                yield AgentStatusWidget(id="status")
                yield PerceptionWidget(id="sensors")
                yield DecisionWidget(id="decision")
                yield LegendWidget(id="legend")
                yield EndGameOverlay(id="endgame")
        yield RetroFooter(id="footer")
        with Container(id="overlay-too-small"):
            yield TooSmallNotice(id="too-small")

    def on_mount(self) -> None:
        known = self.query_one("#map-known", PixelMapWidget)
        known.border_title = KNOWN_MAP_TITLE
        real = self.query_one("#map-real", PixelMapWidget)
        real.border_title = REAL_MAP_TITLE
        self.query_one("#status", AgentStatusWidget).border_title = "AGENTE"
        self.query_one("#sensors", PerceptionWidget).border_title = "SENSORES"
        self.query_one("#decision", DecisionWidget).border_title = "DECISÃO"
        self.query_one("#legend", LegendWidget).border_title = "LEGENDA"
        self.query_one("#endgame", EndGameOverlay).border_title = "RESULTADO"
        self._resize_boards()

        self._timer = self.set_interval(self.interval, self._on_tick, pause=True)
        if self._engine.is_over:
            self._finish()
        self.refresh_game_frame()
        self._apply_layout()
        if not self._paused and not self._finished:
            self._timer.resume()

    def on_resize(self, event: events.Resize) -> None:
        """Relayout without restarting the game, duplicating timers, or stepping.

        The event carries the new size; `self.size` is still the previous one
        while the handler runs.
        """

        self._apply_layout(event.size.width, event.size.height)

    # ------------------------------------------------------------------
    # Frame synchronisation
    # ------------------------------------------------------------------

    def refresh_game_frame(self) -> None:
        """Repaint every panel from one consistent turn state."""

        knowledge = self._agent.memory.knowledge
        known_view = build_known_map_view(
            knowledge, self._snapshot.position, self._snapshot.direction
        )
        self.query_one("#map-known", PixelMapWidget).update(render_map(known_view))

        if self._debug_enabled and self._debug_map_source is not None:
            self.query_one("#map-real", PixelMapWidget).update(
                render_map(self._debug_map_source())
            )

        self.query_one("#status", AgentStatusWidget).update(
            render_agent_status(
                self._snapshot,
                turns=self._engine.turns,
                state_label=self.state_label,
                speed_label=self.speed_label,
                seed=self._seed,
                debug_enabled=self._debug_enabled,
            )
        )
        self.query_one("#sensors", PerceptionWidget).update(
            render_sensors(self._snapshot.perception)
        )
        self.query_one("#decision", DecisionWidget).update(
            render_decision(self._agent.last_reason)
        )
        self.query_one("#legend", LegendWidget).update(render_legend())
        self.query_one("#footer", RetroFooter).update(
            render_footer(self.state_label, self.speed_label)
        )

        if self._failure is not None:
            self.query_one("#endgame", EndGameOverlay).update(
                render_failure(self._failure.strip().splitlines()[-1])
            )
        elif self._outcome is not None:
            self.query_one("#endgame", EndGameOverlay).update(
                render_endgame(self._outcome, self._seed)
            )

    # ------------------------------------------------------------------
    # Turn advancement -- at most one engine step is ever in flight
    # ------------------------------------------------------------------

    def _on_tick(self) -> None:
        if self._paused or self._finished or self._failure is not None:
            return
        self.advance_one_turn()

    def advance_one_turn(self) -> bool:
        """Ask the engine for exactly one turn and repaint. Never reentrant."""

        if self._step_in_progress or self._finished or self._failure is not None:
            return False
        if self._engine.is_over:
            self._finish()
            self.refresh_game_frame()
            return False

        self._step_in_progress = True
        try:
            result = self._engine.step()
        except Exception:  # noqa: BLE001 - surfaced to the player, never swallowed
            self._fail(traceback.format_exc())
            return False
        finally:
            self._step_in_progress = False

        self._snapshot = snapshot_after(self._snapshot, result)
        if self._engine.is_over:
            self._finish()
        self.refresh_game_frame()
        return True

    def _finish(self) -> None:
        self._finished = True
        self._paused = True
        if self._timer is not None:
            self._timer.pause()
        if self._outcome is None:
            self._outcome = self._engine.outcome()
        self._apply_layout()

    def _fail(self, report: str) -> None:
        self._failure = report
        self._paused = True
        if self._timer is not None:
            self._timer.pause()
        self.log.error(report)
        self.refresh_game_frame()
        self._apply_layout()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _resize_boards(self) -> None:
        """Size both boards from the agent's actual map dimensions."""

        knowledge = self._agent.memory.knowledge
        width = map_board_width(knowledge.cols) + _BORDER_THICKNESS
        height = map_board_height(knowledge.rows) + _BORDER_THICKNESS
        for board_id in ("#map-known", "#map-real"):
            board = self.query_one(board_id, PixelMapWidget)
            board.styles.width = width
            board.styles.height = height
        # The HUD column stays exactly as tall as the board it sits beside, so a
        # tall terminal leaves space below both instead of stretching one of them.
        self.query_one("#sidebar", Vertical).styles.height = height

    def _apply_layout(self, width: int | None = None, height: int | None = None) -> None:
        """Recompute every visibility decision for the given size and state."""

        width = self.size.width if width is None else width
        height = self.size.height if height is None else height
        stopped = self._finished or self._failure is not None

        self.query_one("#decision", DecisionWidget).display = not stopped
        self.query_one("#legend", LegendWidget).display = not stopped
        self.query_one("#endgame", EndGameOverlay).display = stopped

        too_small = width < MIN_WIDTH or height < MIN_HEIGHT
        self.query_one("#overlay-too-small", Container).display = too_small
        if too_small:
            self.query_one("#too-small", TooSmallNotice).update(
                render_too_small(width, height, MIN_WIDTH, MIN_HEIGHT)
            )
            return

        # Two boards only when both fit at full tile scale, and never at the
        # cost of the summary the player needs once the game is over.
        wide_enough_for_hud = width >= DUAL_MAP_WITH_SIDEBAR_MIN_WIDTH
        dual = (
            self._debug_enabled
            and width >= DUAL_MAP_MIN_WIDTH
            and (not stopped or wide_enough_for_hud)
        )
        self.query_one("#map-known", PixelMapWidget).display = (
            dual or not self._debug_enabled
        )
        self.query_one("#map-real", PixelMapWidget).display = self._debug_enabled
        self.query_one("#sidebar", Vertical).display = not dual or wide_enough_for_hud

    # ------------------------------------------------------------------
    # Controls -- the player drives execution, never the agent's choices
    # ------------------------------------------------------------------

    def action_toggle_pause(self) -> None:
        if self._finished or self._failure is not None:
            return
        self._paused = not self._paused
        if self._timer is not None:
            if self._paused:
                self._timer.pause()
            else:
                self._timer.resume()
        self.refresh_game_frame()

    def action_single_step(self) -> None:
        """Run exactly one turn and always leave the game paused afterwards."""

        if self._finished or self._failure is not None:
            return
        self._paused = True
        if self._timer is not None:
            self._timer.pause()
        if not self.advance_one_turn():
            self.refresh_game_frame()

    def action_toggle_debug(self) -> None:
        if self._debug_map_source is None:
            return
        self._debug_enabled = not self._debug_enabled
        self.refresh_game_frame()
        self._apply_layout()

    def action_faster(self) -> None:
        self._set_speed_index(self._speed_index + 1)

    def action_slower(self) -> None:
        self._set_speed_index(self._speed_index - 1)

    def action_quit_game(self) -> None:
        self.exit(self._outcome)

    def _set_speed_index(self, index: int) -> None:
        index = max(0, min(MAX_SPEED_INDEX, index))
        if index == self._speed_index:
            return
        self._speed_index = index
        if self._timer is not None:
            self._timer.stop()
        self._timer = self.set_interval(self.interval, self._on_tick, pause=True)
        if not self._paused and not self._finished and self._failure is None:
            self._timer.resume()
        self.refresh_game_frame()
