import uuid
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from pydantic import BaseModel

from agent.ai.combat_graph import build_combat_graph
from agent.models.config import Config
from agent.models.state import State


class GameResult(BaseModel):
    """Result from a game backend operation."""

    state: State
    interrupt: Any | None
    done: bool


class GameBackend:
    """Handles all game logic and LangGraph interactions."""

    def __init__(self, initial_state: State, config: Config) -> None:
        self.initial_state = initial_state.model_copy(deep=True)
        self.combat_graph = build_combat_graph(config=config.agent)
        self.thread_id = str(uuid.uuid4())
        self.started = False
        self.recursion_limit = 20

    def reset(self) -> State:
        """Reset the game to initial state."""
        self.started = False
        self.thread_id = str(uuid.uuid4())
        return self.initial_state.model_copy(deep=True)

    def _get_config(self) -> RunnableConfig:
        """Get the runnable config for this game session."""
        return RunnableConfig(recursion_limit=self.recursion_limit, configurable={"thread_id": self.thread_id})

    async def start_game(self, state: State) -> GameResult:
        """Start a new game session."""
        config = self._get_config()
        result = await self.combat_graph.ainvoke(state, config)
        self.started = True

        return self._process_result(result)

    async def submit_command(self, command: str, state: State) -> GameResult:
        """Submit a user command and process the response."""
        config = self._get_config()

        # Resume the last interrupt
        result = await self.combat_graph.ainvoke(Command(resume=command), config)
        state = State.model_validate(result)

        # If not done, continue execution until next interrupt
        if not state.done:
            result = await self.combat_graph.ainvoke(state, config)

        return self._process_result(result)

    def _process_result(self, result: dict) -> GameResult:
        """Process a graph result into a GameResult."""
        state = State.model_validate(result)
        interrupt = result.get("__interrupt__")

        return GameResult(state=state, interrupt=interrupt[0].value if interrupt else None, done=state.done)
