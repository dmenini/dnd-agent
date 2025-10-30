import asyncio
from asyncio import Queue

from langchain_core.runnables import RunnableConfig
from textual._path import CSSPathType
from textual.app import App, ComposeResult
from textual.command import CommandInput
from textual.containers import Horizontal, Vertical
from textual.driver import Driver
from textual.widgets import Input

from agent.ai.graph import build_graph
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
        self._state = initial_state
        self._log_panel: LogPanel | None = None
        self._map_panel: MapPanel | None = None
        self._char_panel: CharacterPanel | None = None
        self._command_input: Input | None = None
        self.input_queue: Queue = asyncio.Queue()
        super().__init__(driver_class, css_path, watch_css, ansi_color)

        self.graph = build_graph(config=config.agent)

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

            self._command_input = CommandInput(classes="inp", placeholder="Press ENTER to start game...")
            yield self.command_input

    def on_mount(self) -> None:
        if self._state:
            self.update_state(self._state)

    def update_state(self, state: State) -> None:
        """Render a new state."""
        self.map_panel.update_state(state)
        self.log_panel.update_state(state)
        self.char_panel.update_state(state)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        command = event.value.strip()
        event.input.value = ""
        event.input.refresh()

        # Store command directly in the state
        self._state.command = command

        # Run one graph step
        await self.advance_graph()

    async def advance_graph(self) -> None:
        """Manually step the graph."""
        self.command_input.placeholder = "Thinking..."
        self.command_input.refresh()

        state = await self.graph.ainvoke(
            self._state,
            RunnableConfig(recursion_limit=20),
        )
        self._state = State.model_validate(state)

        self.update_state(self._state)
        placeholder = (
            f"What should {self._state.current_actor.name} do? (ENTER to let AI decide)"
            if self._state.is_player_turn
            else "Enemy's turn, press ENTER to continue"
        )
        self.command_input.placeholder = placeholder
        self.command_input.refresh()
