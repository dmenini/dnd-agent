import uuid
from typing import TYPE_CHECKING

from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver

from agent.ai.character_creation.tools import (
    finalize_character,
    finalize_party,
    get_class_options,
    get_party_status,
    save_base_character,
    save_player_selections,
)
from agent.ai.components import create_llm
from agent.character.abilities import SkillType
from agent.character.builder import CharacterBuilder, CharacterSelections
from agent.jobs.base import JobType
from agent.models.config import AgentConfig, Config

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph

DEFAULT_PARTY_NAME = "Players"


class CharacterCreationAgent:
    """Handles natural dialogue flow for creating multiple characters with detailed selections."""

    def __init__(self, config: AgentConfig, max_players: int = 2) -> None:
        llm = create_llm(config.llm)
        self.max_players = max_players
        self.mock_character = config.mock_character
        self.party = DEFAULT_PARTY_NAME

        # State
        self.characters: list[CharacterBuilder] = []
        self._thread_id = str(uuid.uuid4())
        self.done = False
        self.started = False

        # Track current character being built
        self.current_builder: CharacterBuilder | None = None

        tools = self._create_tools()

        self.agent: CompiledStateGraph = create_agent(
            model=llm,
            tools=tools,
            system_prompt=config.prompts.character_builder.format(dm=config.prompts.dm),
            checkpointer=MemorySaver(),
        )
        self.greeting_prompt = "Greet the player explaining who you are and what's the first step in their journey."

    @property
    def has_started(self) -> bool:
        """Check if party creation has started."""
        return self.started

    @property
    def is_done(self) -> bool:
        """Check if party creation is complete."""
        return self.done or len(self.characters) == self.max_players

    @property
    def current_character(self) -> CharacterBuilder | None:
        """Get last created character."""
        return self.characters[-1] if self.characters else None

    def _create_tools(self) -> list:
        """Create the tools for the agent."""

        @tool
        def get_class_options_tool(job_type: JobType) -> str:
            """
            Get available options for a character class (skills, equipment, and features).

            Returns:
                Formatted string describing all available options.
            """
            return get_class_options(job_type)

        @tool
        def save_character_tool(character: CharacterBuilder) -> str:
            """
            Never call this tool without player confirmation!

            Persist the base character information. Behaves like a PUT.
            After this, guide the player through selecting skills, equipment, and features.

            Returns:
                Next steps message.
            """
            return save_base_character(self, character)

        @tool
        def save_player_selections_tool(selections: CharacterSelections) -> str:
            """
            Never call this tool without player confirmation!

            Persist skills, equipment, and features that the player chose. Behaves like a PUT.
            Requires the character builder previously initialized for this character.

            Returns:
                Next steps message
            """
            return save_player_selections(self, selections)

        @tool
        def finalize_character_tool() -> str:
            """
            Call this after all narrative and mechanical choices (skills, equipment, features) are made
            to finalize the creation of the current character.

            Returns:
                Confirmation message
            """
            return finalize_character(self)

        @tool
        def get_party_status_tool() -> str:
            """
            Get the current status of party creation.

            Returns:
                Summary of current characters and maximum allowed.
            """
            return get_party_status(self)

        @tool
        def finalize_party_tool() -> str:
            """
            Finalize the character creation process.
            Call this when the player is done creating characters or maximum is reached.

            Returns:
                Summary of the created party.
            """
            return finalize_party(self)

        return [
            get_class_options_tool,
            save_character_tool,
            save_player_selections_tool,
            finalize_character_tool,
            get_party_status_tool,
            finalize_party_tool,
        ]

    def reset(self) -> None:
        self._thread_id = str(uuid.uuid4())
        self.characters = []
        self.current_builder = None
        self.done = False
        self.started = False

    def create_snapshot(self) -> dict:
        """Create a complete snapshot of the current state."""
        return {
            "thread_id": self._thread_id,
            "characters": self.characters,
            "current_builder": self.current_builder,
            "done": self.done,
            "started": self.started,
        }

    def load_snapshot(self, snapshot: dict) -> None:
        """Load a snapshot, restoring state."""
        self.characters = snapshot["characters"]
        self.current_builder = snapshot["current_builder"]
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
            self.characters = [default_char]
            self.done = True
            return f"The default hero {default_char.name} was created!"

        config = RunnableConfig(configurable={"thread_id": self._thread_id})

        messages = [("system", self.greeting_prompt)] if not user_input else [("user", user_input)]

        response = await self.agent.ainvoke({"messages": messages}, config=config)
        return response["messages"][-1].content

    def run(self) -> None:
        config = RunnableConfig(configurable={"thread_id": "character_creation_session"})

        # Start the conversation
        for event in self.agent.stream(
            {"messages": [("system", self.greeting_prompt)]}, config=config, stream_mode="values"
        ):
            if "messages" in event:
                event["messages"][-1].pretty_print()

        self.started = True

        # Interactive loop
        while not self.done:
            user_input = input("\nYou: ").strip()

            if user_input.lower() in ["quit", "exit"]:
                print("\nExiting character creation.")
                break

            for event in self.agent.stream({"messages": [("user", user_input)]}, config=config, stream_mode="values"):
                if "messages" in event:
                    event["messages"][-1].pretty_print()


if __name__ == "__main__":
    from pathlib import Path

    import yaml  # type: ignore[import-untyped]

    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    with config_path.open() as fp:
        _config = yaml.safe_load(fp)
        _config = Config.model_validate(_config)

    agent = CharacterCreationAgent(_config.agent)
    agent.run()
