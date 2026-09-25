"""Persistent retro Textual game with setup, restart, manual play, and animation."""

from __future__ import annotations

import traceback

from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Static

from wumpus.domain import Action, AgentObservation
from wumpus.game.config import GameConfig
from wumpus.game.engine import GameEngine, GameOutcome
from wumpus.ui.retro_animation import (
    ANIMATION_FRAME_INTERVAL,
    AnimationController,
    AnimationEvent,
    build_initial_sensor_events,
    build_intro_events,
    build_turn_events,
)
from wumpus.ui.retro_map import map_board_height, map_board_width, render_map
from wumpus.ui.retro_panels import (
    DECISION_TITLES,
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
from wumpus.ui.retro_session import (
    DebugMapSource,
    GameMode,
    GameSession,
    SessionFactory,
    SessionSettings,
)
from wumpus.ui.retro_setup import SetupScreen
from wumpus.ui.retro_state import (
    DEFAULT_SPEED_INDEX,
    MAX_SPEED_INDEX,
    SPEED_INTERVALS,
    AgentPresentationSource,
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

HEADER_HEIGHT = 3
FOOTER_HEIGHT = 1
SIDEBAR_WIDTH = 46
_BORDER_THICKNESS = 2
MAP_PANEL_WIDTH = map_board_width(6) + _BORDER_THICKNESS
MAP_PANEL_HEIGHT = map_board_height(6) + _BORDER_THICKNESS
MIN_WIDTH = MAP_PANEL_WIDTH + SIDEBAR_WIDTH
MIN_HEIGHT = HEADER_HEIGHT + MAP_PANEL_HEIGHT + FOOTER_HEIGHT
DUAL_MAP_MIN_WIDTH = 176
DUAL_MAP_WITH_SIDEBAR_MIN_WIDTH = 2 * MAP_PANEL_WIDTH + SIDEBAR_WIDTH

STATE_RUNNING = "RUNNING"
STATE_PAUSED = "PAUSED"
STATE_MANUAL = "JOGADOR"
STATE_FINISHED = "FINISHED"
STATE_ERROR = "ERROR"


class RetroHeader(Static):
    pass


class PixelMapWidget(Static):
    pass


class AgentStatusWidget(Static):
    pass


class PerceptionWidget(Static):
    pass


class DecisionWidget(Static):
    pass


class LegendWidget(Static):
    pass


class RetroFooter(Static):
    pass


class EndGameOverlay(Static):
    pass


class TooSmallNotice(Static):
    pass


class GameScreen(Screen[None]):
    """One match; persistent widgets and exactly one game/animation timer pair."""

    CSS = f"""
    GameScreen {{ background: {RETRO_BACKGROUND}; color: {RETRO_TEXT}; layout: vertical; overflow: hidden; }}
    #header {{ height: {HEADER_HEIGHT}; border: round {RETRO_BORDER}; background: {RETRO_PANEL_BACKGROUND}; content-align: center middle; }}
    #game-area {{ height: 1fr; layout: horizontal; align: center top; overflow: hidden; }}
    #map-known, #map-real {{ width: {MAP_PANEL_WIDTH}; height: {MAP_PANEL_HEIGHT}; border: round {RETRO_BORDER}; background: {RETRO_BACKGROUND}; overflow: hidden; }}
    #map-real {{ border: round {RETRO_DEBUG}; display: none; }}
    #sidebar {{ width: {SIDEBAR_WIDTH}; height: {MAP_PANEL_HEIGHT}; layout: vertical; overflow: hidden; }}
    #sidebar Static {{ border: round {RETRO_BORDER}; background: {RETRO_PANEL_BACKGROUND}; padding: 0 1; overflow: hidden; }}
    #status {{ height: 15; }}
    #sensors {{ height: 8; }}
    #decision {{ height: 1fr; }}
    #legend {{ height: 12; }}
    #endgame {{ height: 1fr; border: double {RETRO_BORDER}; display: none; }}
    #footer {{ height: {FOOTER_HEIGHT}; background: {RETRO_PANEL_BACKGROUND}; color: {RETRO_TEXT_DIM}; }}
    #overlay-too-small {{ layer: overlay; width: 100%; height: 100%; align: center middle; background: {RETRO_BACKGROUND}; display: none; }}
    #too-small {{ width: 44; height: auto; border: round {RETRO_BORDER}; background: {RETRO_PANEL_BACKGROUND}; padding: 1 2; }}
    """

    BINDINGS = [
        ("p", "toggle_pause", "PAUSE"), ("space", "toggle_pause", "PAUSE"),
        ("n", "single_step", "STEP"), ("d", "toggle_debug", "DEBUG"),
        ("plus", "faster", "FASTER"), ("equals_sign", "faster", "FASTER"),
        ("minus", "slower", "SLOWER"), ("underscore", "slower", "SLOWER"),
        ("up", "move_forward", "MOVER"), ("left", "turn_left", "VIRAR"),
        ("right", "turn_right", "VIRAR"), ("g", "grab", "PEGAR"),
        ("f", "shoot", "ATIRAR"), ("e", "climb", "SUBIR"),
        ("r", "restart", "RESTART"), ("q", "quit_game", "QUIT"),
    ]

    def __init__(self, session: GameSession, *, speed_index: int,
                 start_paused: bool, debug_enabled: bool,
                 animations_enabled: bool = True) -> None:
        super().__init__()
        self.session = session
        self._engine = session.engine
        self._agent = session.presentation_source
        self._snapshot = initial_snapshot(session.initial_observation)
        self._speed_index = max(0, min(MAX_SPEED_INDEX, speed_index))
        self._paused = start_paused or session.is_manual
        self._debug_enabled = debug_enabled and session.debug_map_source is not None
        self._finished = False
        self._outcome: GameOutcome | None = None
        self._step_in_progress = False
        self._failure: str | None = None
        self._game_timer = None
        self._animation_timer = None
        self._animations_enabled = animations_enabled
        self.animation_controller = AnimationController()
        self._finish_after_animation = False

    @property
    def interval(self) -> float:
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
        return self._failure

    @property
    def state_label(self) -> str:
        if self._failure is not None:
            return STATE_ERROR
        if self._finished:
            return STATE_FINISHED
        if self.session.is_manual:
            return STATE_MANUAL
        return STATE_PAUSED if self._paused else STATE_RUNNING

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
        self.query_one("#map-known", PixelMapWidget).border_title = KNOWN_MAP_TITLE
        self.query_one("#map-real", PixelMapWidget).border_title = REAL_MAP_TITLE
        self.query_one("#status", AgentStatusWidget).border_title = "AGENTE"
        self.query_one("#sensors", PerceptionWidget).border_title = "SENSORES"
        self.query_one("#decision", DecisionWidget).border_title = DECISION_TITLES[self.session.mode]
        self.query_one("#legend", LegendWidget).border_title = "LEGENDA"
        self.query_one("#endgame", EndGameOverlay).border_title = "RESULTADO"
        self._resize_boards()
        self._game_timer = self.set_interval(self.interval, self._on_game_tick, pause=True)
        self._animation_timer = self.set_interval(ANIMATION_FRAME_INTERVAL, self._on_animation_tick, pause=True)
        if self._engine.is_over:
            self._finish()
        elif self._animations_enabled:
            self._play(build_intro_events())
            self.animation_controller.enqueue(
                build_initial_sensor_events(self._snapshot.perception)
            )
        elif not self._paused and not self.session.is_manual:
            self._game_timer.resume()
        self.refresh_game_frame()
        self._apply_layout()

    def on_unmount(self) -> None:
        self.animation_controller.cancel()
        for timer in (self._game_timer, self._animation_timer):
            if timer is not None:
                timer.stop()

    def on_resize(self, event: events.Resize) -> None:
        self._apply_layout(event.size.width, event.size.height)

    def refresh_game_frame(self) -> None:
        frame = self.animation_controller.frame
        known_view = build_known_map_view(self._agent.memory.knowledge,
                                          self._snapshot.position,
                                          self._snapshot.direction)
        self.query_one("#map-known", PixelMapWidget).update(
            render_map(known_view, frame.overlay if frame is not None else None)
        )
        if self._debug_enabled and self.session.debug_map_source is not None:
            self.query_one("#map-real", PixelMapWidget).update(render_map(self.session.debug_map_source()))
        self.query_one("#header", RetroHeader).update(render_header(frame.banner if frame else None))
        self.query_one("#status", AgentStatusWidget).update(
            render_agent_status(self._snapshot, turns=self._engine.turns,
                                state_label=self.state_label, speed_label=self.speed_label,
                                seed=self.session.settings.seed,
                                debug_enabled=self._debug_enabled,
                                mode=self.session.mode,
                                config=self.session.settings.config)
        )
        self.query_one("#sensors", PerceptionWidget).update(
            render_sensors(self._snapshot.perception, frame.phases if frame else None)
        )
        self.query_one("#decision", DecisionWidget).update(
            render_decision(self._agent.last_reason, self.session.mode)
        )
        self.query_one("#legend", LegendWidget).update(render_legend())
        self.query_one("#footer", RetroFooter).update(
            render_footer(self.state_label, self.speed_label, self.session.mode)
        )
        self._apply_frame_border(frame.border_flash if frame else None)
        if self._failure is not None:
            self.query_one("#endgame", EndGameOverlay).update(
                render_failure(self._failure.strip().splitlines()[-1])
            )
        elif self._outcome is not None:
            self.query_one("#endgame", EndGameOverlay).update(
                render_endgame(self._outcome, self.session.settings.seed)
            )

    def _on_game_tick(self) -> None:
        if (self.session.is_manual or self._paused or self._finished
                or self._failure is not None or self.animation_controller.busy):
            return
        self.advance_one_turn()

    def advance_one_turn(self) -> bool:
        if (self._step_in_progress or self._finished or self._failure is not None
                or self.animation_controller.busy):
            return False
        if self._engine.is_over:
            self._finish()
            self.refresh_game_frame()
            return False
        old_position = self._snapshot.position
        old_perception = self._snapshot.perception
        self._step_in_progress = True
        if self._game_timer is not None:
            self._game_timer.pause()
        try:
            result = self._engine.step()
        except Exception:  # noqa: BLE001
            self._fail(traceback.format_exc())
            return False
        finally:
            self._step_in_progress = False
        self._snapshot = snapshot_after(self._snapshot, result)
        self._finish_after_animation = self._engine.is_over
        events = build_turn_events(
            result, previous_position=old_position,
            previous_perception=old_perception,
            bounds=(self._agent.memory.knowledge.rows, self._agent.memory.knowledge.cols),
        )
        if self._animations_enabled and events:
            self._play(events)
        elif self._finish_after_animation:
            self._finish()
        elif not self._paused and not self.session.is_manual and self._game_timer is not None:
            self._game_timer.resume()
        self.refresh_game_frame()
        return True

    def _play(self, events: tuple[AnimationEvent, ...]) -> None:
        self.animation_controller.enqueue(events)
        if self._game_timer is not None:
            self._game_timer.pause()
        if self._animation_timer is not None:
            self._animation_timer.resume()

    def _on_animation_tick(self) -> None:
        if self.animation_controller.advance():
            self.refresh_game_frame()
            return
        if self._animation_timer is not None:
            self._animation_timer.pause()
        if self._finish_after_animation:
            self._finish_after_animation = False
            self._finish()
        elif not self._paused and not self.session.is_manual and self._game_timer is not None:
            self._game_timer.resume()
        self.refresh_game_frame()

    def _finish(self) -> None:
        self._finished = True
        self._paused = True
        if self._game_timer is not None:
            self._game_timer.pause()
        if self._outcome is None:
            self._outcome = self._engine.outcome()
        self._apply_layout()

    def _fail(self, report: str) -> None:
        self._failure = report
        self._paused = True
        if self._game_timer is not None:
            self._game_timer.pause()
        self.log.error(report)
        self.refresh_game_frame()
        self._apply_layout()

    def _resize_boards(self) -> None:
        knowledge = self._agent.memory.knowledge
        width = map_board_width(knowledge.cols) + _BORDER_THICKNESS
        height = map_board_height(knowledge.rows) + _BORDER_THICKNESS
        for board_id in ("#map-known", "#map-real"):
            board = self.query_one(board_id, PixelMapWidget)
            board.styles.width = width
            board.styles.height = height
        self.query_one("#sidebar", Vertical).styles.height = height

    def _apply_layout(self, width: int | None = None, height: int | None = None) -> None:
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
        wide_hud = width >= DUAL_MAP_WITH_SIDEBAR_MIN_WIDTH
        dual = self._debug_enabled and width >= DUAL_MAP_MIN_WIDTH and (not stopped or wide_hud)
        self.query_one("#map-known", PixelMapWidget).display = dual or not self._debug_enabled
        self.query_one("#map-real", PixelMapWidget).display = self._debug_enabled
        self.query_one("#sidebar", Vertical).display = not dual or wide_hud

    def _apply_frame_border(self, flash: str | None) -> None:
        colour = flash or RETRO_BORDER
        self.query_one("#map-known", PixelMapWidget).styles.border = ("round", colour)
        self.query_one("#sensors", PerceptionWidget).styles.border = ("round", colour)

    def action_toggle_pause(self) -> None:
        if self.session.is_manual or self._finished or self._failure is not None:
            return
        self._paused = not self._paused
        if self._game_timer is not None and not self.animation_controller.busy:
            (self._game_timer.pause if self._paused else self._game_timer.resume)()
        self.refresh_game_frame()

    def action_single_step(self) -> None:
        if self.session.is_manual or self._finished or self._failure is not None:
            return
        self._paused = True
        if self._game_timer is not None:
            self._game_timer.pause()
        if not self.advance_one_turn():
            self.refresh_game_frame()

    def action_toggle_debug(self) -> None:
        if self.session.debug_map_source is None:
            return
        self._debug_enabled = not self._debug_enabled
        self.refresh_game_frame()
        self._apply_layout()

    def action_faster(self) -> None:
        if not self.session.is_manual:
            self._set_speed_index(self._speed_index + 1)

    def action_slower(self) -> None:
        if not self.session.is_manual:
            self._set_speed_index(self._speed_index - 1)

    def action_move_forward(self) -> None:
        self._manual_action(Action.MOVE_FORWARD)

    def action_turn_left(self) -> None:
        self._manual_action(Action.TURN_LEFT)

    def action_turn_right(self) -> None:
        self._manual_action(Action.TURN_RIGHT)

    def action_grab(self) -> None:
        self._manual_action(Action.GRAB)

    def action_shoot(self) -> None:
        self._manual_action(Action.SHOOT)

    def action_climb(self) -> None:
        self._manual_action(Action.CLIMB)

    def _manual_action(self, action: Action) -> None:
        if (not self.session.is_manual or self.session.manual_action_submitter is None
                or self._finished or self._failure is not None
                or self.animation_controller.busy or self._step_in_progress):
            return
        self.session.manual_action_submitter(action)
        self.advance_one_turn()

    def action_restart(self) -> None:
        self.animation_controller.cancel()
        if self.session.manual_action_clearer is not None:
            self.session.manual_action_clearer()
        for timer in (self._game_timer, self._animation_timer):
            if timer is not None:
                timer.stop()
        self.app.return_to_setup(self.session.settings)  # type: ignore[attr-defined]

    def action_quit_game(self) -> None:
        self.app.exit(self._outcome)

    def _set_speed_index(self, index: int) -> None:
        index = max(0, min(MAX_SPEED_INDEX, index))
        if index == self._speed_index:
            return
        self._speed_index = index
        if self._game_timer is not None:
            self._game_timer.stop()
        self._game_timer = self.set_interval(self.interval, self._on_game_tick, pause=True)
        if (not self._paused and not self._finished and self._failure is None
                and not self.animation_controller.busy):
            self._game_timer.resume()
        self.refresh_game_frame()


class RetroGameApp(App[GameOutcome | None]):
    """Swap the pre-game screen for independently assembled safe sessions."""

    CSS = f"Screen {{ background: {RETRO_BACKGROUND}; overflow: hidden; }}"
    BINDINGS = [Binding("q", "quit_application", "QUIT", priority=True)]

    def __init__(self, *, session_factory: SessionFactory | None = None,
                 seed: int | None = None, speed_index: int = DEFAULT_SPEED_INDEX,
                 start_paused: bool = False, debug_enabled: bool = False,
                 engine: GameEngine | None = None,
                 agent: AgentPresentationSource | None = None,
                 initial_observation: AgentObservation | None = None,
                 debug_map_source: DebugMapSource | None = None) -> None:
        super().__init__()
        self._session_factory = session_factory
        self._seed = seed
        self._speed_index = speed_index
        self._start_paused = start_paused
        self._debug_enabled = debug_enabled
        self._game_screen: GameScreen | None = None
        self._legacy_session: GameSession | None = None
        if engine is not None and agent is not None and initial_observation is not None:
            settings = SessionSettings(
                mode=GameMode.AUTONOMOUS, seed=seed,
                game_config=GameConfig(rows=agent.memory.knowledge.rows,
                                       cols=agent.memory.knowledge.cols),
            )
            self._legacy_session = GameSession(
                engine=engine, presentation_source=agent,
                initial_observation=initial_observation,
                mode=GameMode.AUTONOMOUS, settings=settings,
                debug_map_source=debug_map_source,
            )
        elif session_factory is None:
            raise TypeError("RetroGameApp requires a session_factory or a complete session")

    def on_mount(self) -> None:
        if self._legacy_session is not None:
            self._show_game(
                self._legacy_session,
                animations_enabled=False,
                initial=True,
            )
        else:
            self.push_screen(SetupScreen(seed=self._seed))

    def start_session(self, settings: SessionSettings) -> None:
        assert self._session_factory is not None
        try:
            session = self._session_factory(settings)
        except Exception as error:  # noqa: BLE001
            self.query_one("#setup-error", Static).update(f"CONFIGURAÇÃO INVÁLIDA\n{error}")
            return
        self._show_game(session, animations_enabled=True)

    def return_to_setup(self, settings: SessionSettings) -> None:
        self._game_screen = None
        self.switch_screen(SetupScreen(seed=settings.seed, config=settings.config,
                                       mode=settings.mode))

    def action_quit_application(self) -> None:
        outcome = self._game_screen.outcome if self._game_screen is not None else None
        self.exit(outcome)

    def _show_game(
        self,
        session: GameSession,
        *,
        animations_enabled: bool,
        initial: bool = False,
    ) -> None:
        self._game_screen = GameScreen(
            session, speed_index=self._speed_index,
            start_paused=self._start_paused,
            debug_enabled=self._debug_enabled,
            animations_enabled=animations_enabled,
        )
        if initial:
            self.push_screen(self._game_screen)
        else:
            self.switch_screen(self._game_screen)

    @property
    def game_screen(self) -> GameScreen | None:
        return self._game_screen

    @property
    def interval(self) -> float:
        return self._game().interval

    @property
    def speed_index(self) -> int:
        return self._game().speed_index

    @property
    def paused(self) -> bool:
        return self._game().paused

    @property
    def finished(self) -> bool:
        return self._game().finished

    @property
    def debug_enabled(self) -> bool:
        return self._game().debug_enabled

    @property
    def outcome(self) -> GameOutcome | None:
        return self._game().outcome

    @property
    def failure(self) -> str | None:
        return self._game().failure

    @property
    def state_label(self) -> str:
        return self._game().state_label

    def _game(self) -> GameScreen:
        if self._game_screen is None:
            raise RuntimeError("No game session is active")
        return self._game_screen
