import asyncio
from asyncio import Queue

from langchain_core.runnables import RunnableConfig
from textual._path import CSSPathType
from textual.app import App, ComposeResult
from textual.command import CommandInput
from textual.containers import Horizontal, Vertical
from textual.driver import Driver
from textual.widgets import Footer, Header, Input, Rule

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
        self.input_queue: Queue = asyncio.Queue()
        super().__init__(driver_class, css_path, watch_css, ansi_color)

        self.graph = build_graph(config=config.agent)
        self.title = "DnD Agent"

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
        self.update_state(self._state)
        self.theme = "monokai"

    def update_state(self, state: State) -> None:
        """Render a new state."""
        self.query_one("#map", MapPanel).update_state(state)
        self.query_one("#logs", LogPanel).update_state(state)
        self.query_one("#character", CharacterPanel).update_state(state)

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
        command_input = self.query_one("#user-input", Input)
        command_input.placeholder = "Thinking..."
        command_input.refresh()

        def report_update(state: State) -> None:
            self._state = state
            self.update_state(self._state)

            placeholder = (
                f"What should {self._state.current_actor.name} do? (ENTER to let AI decide)"
                if self._state.is_player_turn
                else "Enemy's turn, press ENTER to continue"
            )
            command_input.placeholder = placeholder
            command_input.refresh()

        self._state.update_callback = report_update

        state = await self.graph.ainvoke(
            self._state,
            RunnableConfig(recursion_limit=20),
        )
        self._state = State.model_validate(state)
        self.update_state(self._state)
