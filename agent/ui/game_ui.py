import queue

from textual._path import CSSPathType
from textual.app import App, ComposeResult
from textual.command import CommandInput
from textual.containers import Horizontal, Vertical
from textual.driver import Driver
from textual.widgets import Input

from agent.models.state import State
from agent.ui.character_panel import CharacterPanel
from agent.ui.log_panel import LogPanel
from agent.ui.map_panel import MapPanel


class GameUI(App):
    CSS = """
    Screen {
        layout: horizontal;
    }

    .left {
        width: 70%;
        layout: vertical;
    }

    .map {
        height: 40%;
        border: solid white;
    }

    .logs {
        height: 50%;
        border: solid yellow;
    }

    .character {
        height: 90%;
        width: 30%;
        border: solid green;
    }
    
    .inp {
        height: 10%;
        border: solid red;
    }
    
    """

    def __init__(
        self,
        driver_class: type[Driver] | None = None,
        css_path: CSSPathType | None = None,
        watch_css: bool = False,
        ansi_color: bool = False,
        initial_state: State | None = None,
        on_command=None,
    ) -> None:
        self._external_state = initial_state
        self.log_panel = None
        self.map_panel = None
        self.char_panel = None
        self.command_input = None
        self.on_command = on_command
        self.input_queue = queue.Queue()
        super().__init__(driver_class, css_path, watch_css, ansi_color)

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal():
                with Vertical(classes="left"):
                    self.map_panel = MapPanel(classes="map")
                    self.log_panel = LogPanel(classes="logs")
                    yield self.map_panel
                    yield self.log_panel

                self.char_panel = CharacterPanel(classes="character")
                yield self.char_panel

            self.command_input = CommandInput(classes="inp", placeholder="Enter your command...")
            yield self.command_input

    def on_mount(self) -> None:
        if self._external_state:
            self.update_state(self._external_state)

    def update_state(self, state: State) -> None:
        """Render a new state."""
        self.map_panel.update_state(state)
        self.log_panel.update_state(state)
        self.char_panel.update_state(state)

    def show_prompt(self, prompt: str) -> None:
        self.command_input.update(f"[bold yellow]{prompt}[/]")

    def wait_for_input(self) -> str:
        """Blocks until player enters a command."""
        return self.input_queue.get()  # Waits synchronously

    def on_input_submitted(self, event: Input.Submitted) -> None:
        command = event.value.strip()
        event.input.value = ""
        self.input_queue.put(command)  # Resume whoever is waiting

