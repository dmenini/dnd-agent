from textual import work
from textual._path import CSSPathType
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.driver import Driver
from textual.widgets import Footer, Header, Input, Rule

from agent.ai.backend import GameBackend, GamePhase, GameResult
from agent.models.config import Config
from agent.models.state import State
from agent.ui.character_panel import CharacterPanel
from agent.ui.log_panel import LogPanel
from agent.ui.map_panel import MapPanel


class GameUI(App):
    CSS_PATH = "style.tcss"

    def __init__(
        self,
        *,
        initial_state: State,
        config: Config,
        driver_class: type[Driver] | None = None,
        css_path: CSSPathType | None = None,
        watch_css: bool = False,
        ansi_color: bool = False,
    ) -> None:
        super().__init__(driver_class, css_path, watch_css, ansi_color)
        self.state = initial_state.model_copy(deep=True)
        self.backend = GameBackend(initial_state, config)

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with Horizontal():
                with Vertical():
                    yield MapPanel(id="map", classes="map")
                    yield Rule()
                    yield LogPanel(id="logs", classes="logs")

                yield Rule(orientation="vertical")
                yield CharacterPanel(id="character", classes="character")

            yield Input(id="user-input", classes="inp", placeholder="Press ENTER to start game...")
        yield Footer()

    def on_mount(self) -> None:
        self.update_state(self.state)
        self.theme = "monokai"

    def update_state(self, state: State) -> None:
        """Render a new state."""
        self.state = state
        self.query_one("#map", MapPanel).update_state(state)
        self.query_one("#logs", LogPanel).update_state(state)
        self.query_one("#character", CharacterPanel).update_state(state)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission."""
        command = event.value.strip()

        # Clear input and show thinking state
        event.input.value = ""
        event.input.placeholder = "Thinking..."
        event.input.disabled = True
        event.input.refresh()

        # Handle game reset
        if self.state.done:
            state = self.backend.reset()
            self.update_state(state)

        # Process command in background
        if self.backend.phase == GamePhase.START:
            self.process_start_game()
        else:
            self.process_command(command)

    @work(thread=True)
    async def process_start_game(self) -> None:
        """Start the game in a background thread."""
        result = await self.backend.start()
        self.call_from_thread(self.handle_game_result, result)

    @work(thread=True)
    async def process_command(self, command: str) -> None:
        """Process a user command in a background thread."""
        result = await self.backend.submit_command(command)
        self.call_from_thread(self.handle_game_result, result)

    def handle_game_result(self, result: GameResult) -> None:
        """Handle the result of a game operation (runs on main thread)."""
        # Update state
        self.update_state(result.state)

        # Update input field
        input_widget = self.query_one("#user-input", Input)
        input_widget.disabled = False

        if result.done:
            input_widget.placeholder = "Press ENTER to start new game..."
        elif result.interrupt:
            input_widget.placeholder = result.interrupt
        else:
            input_widget.placeholder = "Enter command..."

        input_widget.focus()
        input_widget.refresh()
