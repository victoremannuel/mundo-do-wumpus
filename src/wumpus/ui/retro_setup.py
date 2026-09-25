"""Pre-game configuration screen for the retro interface."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, RadioButton, RadioSet, Static

from wumpus.game.config import GameConfig
from wumpus.ui.retro_session import (
    INVALID_CONFIG_TITLE,
    GameMode,
    SessionSettings,
    validate_cave,
)
from wumpus.ui.symbols import (
    RETRO_BACKGROUND,
    RETRO_BORDER,
    RETRO_PANEL_BACKGROUND,
    RETRO_TEXT,
    RETRO_TEXT_DIM,
)


COUNT_FIELDS = (
    ("WUMPUS", "wumpus-count", "wumpus_count"),
    ("POÇOS", "pit-count", "pit_count"),
    ("OUROS", "gold-count", "gold_count"),
    ("MORCEGOS", "bat-count", "bat_count"),
)


class SetupScreen(Screen[None]):
    """Require an explicit mode and validate counts before creating a game."""

    CSS = f"""
    SetupScreen {{
        background: {RETRO_BACKGROUND};
        color: {RETRO_TEXT};
        align: center middle;
        overflow: hidden;
    }}

    #setup-box {{
        width: 58;
        height: 38;
        border: double {RETRO_BORDER};
        background: {RETRO_PANEL_BACKGROUND};
        padding: 1 3;
    }}

    #setup-title {{
        height: 3;
        content-align: center middle;
        text-style: bold;
    }}

    .section-title {{
        margin-top: 1;
        color: {RETRO_TEXT_DIM};
        text-style: bold;
    }}

    #mode-set {{ height: 5; border: none; padding: 0; }}
    .count-row {{ height: 3; align: center middle; }}
    .count-label {{ width: 18; }}
    .count-input {{ width: 10; }}

    #setup-error {{
        height: 4;
        color: red;
        content-align: center middle;
        text-align: center;
    }}

    #setup-actions {{ height: 3; align: center middle; }}
    #start-game {{ margin-right: 2; }}
    """

    BINDINGS = [
        Binding("1", "select_autonomous", "AUTÔNOMO"),
        Binding("2", "select_manual", "JOGADOR"),
        Binding("enter", "start_game", "INICIAR", priority=True),
        Binding("q", "quit_setup", "SAIR", priority=True),
    ]

    def __init__(
        self,
        *,
        seed: int | None,
        config: GameConfig | None = None,
        mode: GameMode | None = None,
    ) -> None:
        super().__init__()
        self.seed = seed
        self.config = config if config is not None else GameConfig()
        self.selected_mode = mode

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="setup-box"):
                yield Static("M U N D O   D O   W U M P U S\nNOVA PARTIDA", id="setup-title")
                yield Label("ESCOLHA O MODO", classes="section-title")
                with RadioSet(id="mode-set"):
                    yield RadioButton("[1] AGENTE AUTÔNOMO", id="mode-autonomous")
                    yield RadioButton("[2] JOGADOR", id="mode-manual")
                yield Label("CONFIGURAÇÃO DA CAVERNA", classes="section-title")
                for label, field_id, attribute in COUNT_FIELDS:
                    with Horizontal(classes="count-row"):
                        yield Label(label, classes="count-label")
                        yield Input(
                            value=str(getattr(self.config, attribute)),
                            id=field_id,
                            classes="count-input",
                            restrict=r"[0-9]*",
                            max_length=2,
                        )
                yield Static("", id="setup-error")
                with Horizontal(id="setup-actions"):
                    yield Button("[ ENTER ] INICIAR", id="start-game", disabled=True)
                    yield Button("[ Q ] SAIR", id="quit-setup")

    def on_mount(self) -> None:
        if self.selected_mode is not None:
            self._select_mode(self.selected_mode)
        else:
            self.query_one("#mode-set", RadioSet).focus()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.pressed.id == "mode-autonomous":
            self.selected_mode = GameMode.AUTONOMOUS
        elif event.pressed.id == "mode-manual":
            self.selected_mode = GameMode.MANUAL
        self.query_one("#start-game", Button).disabled = self.selected_mode is None
        self._show_error("")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start-game":
            self.action_start_game()
        elif event.button.id == "quit-setup":
            self.action_quit_setup()

    def on_input_submitted(self, _event: Input.Submitted) -> None:
        self.action_start_game()

    def action_select_autonomous(self) -> None:
        self._select_mode(GameMode.AUTONOMOUS)

    def action_select_manual(self) -> None:
        self._select_mode(GameMode.MANUAL)

    def action_start_game(self) -> None:
        if self.selected_mode is None:
            self._show_error("Escolha AUTÔNOMO ou JOGADOR antes de iniciar.")
            return
        try:
            values = {
                attribute: int(self.query_one(f"#{field_id}", Input).value)
                for _label, field_id, attribute in COUNT_FIELDS
            }
        except ValueError:
            self._show_error(
                f"{INVALID_CONFIG_TITLE}\nAs quantidades devem ser números inteiros."
            )
            return

        config = GameConfig(**values)
        error = validate_cave(config)
        if error is not None:
            self._show_error(f"{INVALID_CONFIG_TITLE}\n{error}")
            return

        settings = SessionSettings(
            mode=self.selected_mode,
            seed=self.seed,
            game_config=config,
        )
        self.app.start_session(settings)  # type: ignore[attr-defined]

    def action_quit_setup(self) -> None:
        self.app.exit(None)

    def _select_mode(self, mode: GameMode) -> None:
        button_id = "#mode-autonomous" if mode is GameMode.AUTONOMOUS else "#mode-manual"
        self.query_one(button_id, RadioButton).value = True
        self.selected_mode = mode
        self.query_one("#start-game", Button).disabled = False

    def _show_error(self, message: str) -> None:
        self.query_one("#setup-error", Static).update(message)
