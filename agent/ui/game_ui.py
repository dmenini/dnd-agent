import asyncio
from asyncio import Queue

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
    CSS_PATH = "style.tcss"

    def __init__(
        self,
        *,
        driver_class: type[Driver] | None = None,
        css_path: CSSPathType | None = None,
        watch_css: bool = False,
        ansi_color: bool = False,
        initial_state: State | None = None,
    ) -> None:
        self._init_state = initial_state
        self._log_panel: LogPanel | None = None
        self._map_panel: MapPanel | None = None
        self._char_panel: CharacterPanel | None = None
        self._command_input: Input | None = None
        self.input_queue: Queue = asyncio.Queue()
        super().__init__(driver_class, css_path, watch_css, ansi_color)

    @property
    def log_panel(self) -> LogPanel:
        if self._log_panel is None:
            raise ValueError
        return self._log_panel

    @property
    def map_panel(self) -> MapPanel:
        if self._map_panel is None:
            raise ValueError
        return self._map_panel

    @property
    def char_panel(self) -> CharacterPanel:
        if self._char_panel is None:
            raise ValueError
        return self._char_panel

    @property
    def command_input(self) -> Input:
        if self._command_input is None:
            raise ValueError
        return self._command_input

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal():
                with Vertical(classes="left"):
                    self._map_panel = MapPanel(classes="map")
                    self._log_panel = LogPanel(classes="logs")
                    yield self._map_panel
                    yield self._log_panel

                self._char_panel = CharacterPanel(classes="character")
                yield self.char_panel

            self._command_input = CommandInput(classes="inp", placeholder="Enter your command...")
            yield self.command_input

    def on_mount(self) -> None:
        if self._init_state:
            self.update_state(self._init_state)

    def update_state(self, state: State) -> None:
        """Render a new state."""
        self.map_panel.update_state(state)
        self.log_panel.update_state(state)
        self.char_panel.update_state(state)

    def show_prompt(self, prompt: str) -> None:
        """Update the placeholder dynamically."""
        self.command_input.placeholder = prompt
        # Force a redraw so the new placeholder shows immediately
        self.command_input.refresh()

    async def wait_for_input(self) -> str:
        command = await self.input_queue.get()
        self.command_input.value = ""
        self.command_input.placeholder = "Thinking..."
        self.command_input.refresh()
        return command

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        command = event.value.strip()
        await self.input_queue.put(command)
        event.input.value = ""
        event.input.refresh()
