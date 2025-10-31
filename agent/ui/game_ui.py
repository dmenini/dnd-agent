import uuid

from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command
from textual._path import CSSPathType
from textual.app import App, ComposeResult
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
        super().__init__(driver_class, css_path, watch_css, ansi_color)
        self.title = "DnD Agent"

        self._init_state = initial_state.model_copy(deep=True)
        self.state = initial_state.model_copy(deep=True)
        self.graph = build_graph(config=config.agent)

        self.started = False
        self.thread_id = str(uuid.uuid4())

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

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        command = event.value.strip()

        # Acknowledge input by changing placeholder
        event.input.value = ""
        event.input.placeholder = "Thinking..."
        event.input.refresh()

        # Handle new game
        if self.state.done:
            self.started = False
            self.update_state(self._init_state)

        config = RunnableConfig(recursion_limit=20, configurable={"thread_id": self.thread_id})

        # First run - start the graph
        if not self.started:
            result = await self.graph.ainvoke(self.state, config)
            self.started = True

        # User responded - resume last interrupt
        else:
            # Resume the last interrupt (continues thread)
            result = await self.graph.ainvoke(Command(resume=command), config)
            state = State.model_validate(result)
            self.update_state(state)

            if not state.done:
                # Immediately continue execution until the next interrupt
                result = await self.graph.ainvoke(self.state, config)

        state = State.model_validate(result)
        self.update_state(state)

        # If new interrupt, update UI placeholder
        if intr := result.get("__interrupt__"):
            event.input.placeholder = intr[0].value
            event.input.refresh()

        if state.done:
            event.input.placeholder = "Press ENTER to start game..."
            event.input.refresh()
