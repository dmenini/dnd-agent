import operator
import uuid
from typing import Annotated, TYPE_CHECKING

from langchain.agents import AgentState, create_agent
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver

from agent.ai.character_creation.tools import (
    finalize_character,
    finalize_party,
    get_class_options,
    get_party_status,
    save_base_character,
    save_skills,
    save_starting_equipment,
    save_subclass,
)
from agent.ai.components import create_llm
from agent.character.abilities import SkillType
from agent.character.builder import CharacterBuilder, CharacterSelections
from agent.jobs.base import JobType
from agent.models.config import AgentConfig, Config

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph

DEFAULT_PARTY_NAME = "Players"


class CharacterCreationState(AgentState):
    current_builder: CharacterBuilder | None
    party: Annotated[list[CharacterBuilder], operator.add]
    max_players: int
    done: bool


class CharacterCreationAgent:
    """Handles natural dialogue flow for creating multiple characters with detailed selections."""

    def __init__(self, config: AgentConfig, max_players: int = 2) -> None:
        llm = create_llm(config.llm)
        self.max_players = max_players
        self.mock_character = config.mock_character
        self.party_name = DEFAULT_PARTY_NAME

        # State
        self.party: list[CharacterBuilder] = []
        self._thread_id = str(uuid.uuid4())
        self.done = False
        self.started = False

        tools = [
            get_class_options,
            save_base_character,
            save_subclass,
            save_starting_equipment,
            save_skills,
            finalize_character,
            get_party_status,
            finalize_party,
        ]

        self.agent: CompiledStateGraph = create_agent(
            model=llm,
            tools=tools,
            system_prompt=config.prompts.character_builder.format(dm=config.prompts.dm),
            checkpointer=MemorySaver(),
            state_schema=CharacterCreationState,
        )
        self.greeting_prompt = "Greet the player explaining who you are and what's the first step in their journey."

    @property
    def has_started(self) -> bool:
        """Check if party creation has started."""
        return self.started

    @property
    def is_done(self) -> bool:
        """Check if party creation is complete."""
        return self.done or len(self.party) == self.max_players

    @property
    def current_character(self) -> CharacterBuilder | None:
        """Get last created character."""
        return self.party[-1] if self.party else None

    def reset(self) -> None:
        self._thread_id = str(uuid.uuid4())
        self.party = []
        self.done = False
        self.started = False

    def create_snapshot(self) -> dict:
        """Create a complete snapshot of the current state."""
        return {
            "thread_id": self._thread_id,
            "party": self.party,
            "done": self.done,
            "started": self.started,
        }

    def load_snapshot(self, snapshot: dict) -> None:
        """Load a snapshot, restoring state."""
        self.party = snapshot["party"]
        self._thread_id = snapshot["thread_id"]
        self.done = snapshot["done"]
        self.started = snapshot["started"]

    async def respond(self, user_input: str) -> str:
        """Handle one conversational step."""
        self.started = True

        if self.mock_character:
            default_char = CharacterBuilder(
                name="Alfred",
                icon="🧝",
                job=JobType.WIZARD,
                summary="The default Hero of our story.",
                selections=CharacterSelections(skill_proficiencies=[SkillType.ARCANA, SkillType.HISTORY]),
            )
            self.party = [default_char]
            self.done = True
            return f"The default hero {default_char.name} was created!"

        config = RunnableConfig(configurable={"thread_id": self._thread_id})

        messages: list[BaseMessage] = (
            [SystemMessage(content=self.greeting_prompt)] if not user_input else [HumanMessage(content=user_input)]
        )
        input_ = {
            "messages": messages,
            "max_players": self.max_players,
        }
        response = await self.agent.ainvoke(input_, config=config)
        if "party" in response:
            self.party = response["party"]
        if "done" in response:
            self.done = response["done"]
        return response["messages"][-1].content

    def run(self) -> None:
        config = RunnableConfig(configurable={"thread_id": "character_creation_session"})

        # Start the conversation
        input_ = {
            "current_builder": None,
            "messages": [SystemMessage(content=self.greeting_prompt)],
            "max_players": self.max_players,
        }
        for event in self.agent.stream(input_, config=config, stream_mode="values"):
            event["messages"][-1].pretty_print()

        self.started = True

        # Interactive loop
        while not self.done:
            user_input = input("\nYou: ").strip()
            input_ = {
                "messages": [HumanMessage(content=user_input)],  # type: ignore[list-item]
            }
            for event in self.agent.stream(input_, config=config, stream_mode="values"):
                event["messages"][-1].pretty_print()
                if "done" in event:
                    self.done = event["done"]
                if "party" in event:
                    self.party = event["party"]


if __name__ == "__main__":
    from pathlib import Path

    import yaml  # type: ignore[import-untyped]

    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    with config_path.open() as fp:
        _config = yaml.safe_load(fp)
        _config = Config.model_validate(_config)

    agent = CharacterCreationAgent(_config.agent)
    agent.run()
