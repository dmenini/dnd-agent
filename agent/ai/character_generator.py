import uuid

from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver

from agent.ai.components import create_llm
from agent.character.builder import CharacterBuilder
from agent.jobs.base import JobType
from agent.models.config import AgentConfig, Config

DEFAULT_PARTY_NAME = "Players"


class CharacterCreationAgent:
    """Handles natural dialogue flow for creating multiple characters."""

    def __init__(self, config: AgentConfig, max_players: int = 2) -> None:
        llm = create_llm(config.llm)
        self.max_players = max_players
        self.mock_character = config.mock_character
        self.party = DEFAULT_PARTY_NAME

        # State
        self.characters: list[CharacterBuilder] = []
        self._thread_id = str(uuid.uuid4())
        self._done = False
        self._started = False

        tools = self._create_tools()

        self.agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=config.prompts.character_builder.format(dm=config.prompts.dm),
            checkpointer=MemorySaver(),
        )
        self.greeting_prompt = "Greet the player explaining who you are and what's the first step in their journey."

    @property
    def has_started(self) -> bool:
        """Check if party creation has started."""
        return self._started

    @property
    def is_done(self) -> bool:
        """Check if party creation is complete."""
        return self._done or len(self.characters) == self.max_players

    @property
    def current_character(self) -> CharacterBuilder | None:
        """Get last created character."""
        return self.characters[-1] if self.characters else None

    def _create_tools(self) -> list:
        """Create the tools for the agent."""

        @tool
        def create_character(character: CharacterBuilder) -> str:
            """
            Create and save a character with all required information.
            Call this ONLY when you have all the necessary info collected.

            Returns:
                Confirmation message
            """
            self.characters.append(character)
            if len(self.characters) == self.max_players:
                self._done = True
            return f"Character {character} created!"

        @tool
        def get_party_status() -> str:
            """
            Get the current status of party creation.

            Returns:
                Summary of current characters and maximum allowed.
            """
            remaining = self.max_players - len(self.characters)

            if remaining > 0:
                context = f"Players have created {len(self.characters)}/{self.max_players} character(s)"
                for char in self.characters:
                    context += f"\n- {char.name}: {char.summary}"
                context += f"\n\nThey can create {remaining} more."
                return context

            return f"Players have created the maximum of {self.max_players} characters! Party is complete."

        @tool
        def finalize_party() -> str:
            """
            Finalize the character creation process.
            Call this when the player is done creating characters or maximum is reached.

            Returns:
                Summary of the created party
            """
            self._done = True

            context = f"Players have created {len(self.characters)}/{self.max_players} character(s)"
            for char in self.characters:
                context += f"\n- {char.name}: {char.summary}"
            return context

        return [
            create_character,
            get_party_status,
            finalize_party,
        ]

    def reset(self) -> None:
        self.characters = []
        self._thread_id = str(uuid.uuid4())
        self._done = False
        self._started = False

    def create_snapshot(self) -> dict:
        """Create a complete snapshot of the current state."""
        return {
            "characters": self.characters,
            "thread_id": self._thread_id,
            "done": self._done,
            "started": self._started,
        }

    def load_snapshot(self, snapshot: dict) -> None:
        """Load a snapshot, restoring state."""
        self.characters = snapshot["characters"]
        self._thread_id = snapshot["thread_id"]
        self._done = snapshot["done"]
        self._started = snapshot["started"]

    async def respond(self, user_input: str) -> str:
        """Handle one conversational step."""
        self._started = True

        if self.mock_character:
            default_char = CharacterBuilder(
                name="Alfred",
                icon="🧝",
                job=JobType.WIZARD,
                summary="The default Hero of our story.",
            )
            self.characters = [default_char]
            self._done = True
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

        self._started = True

        # Interactive loop
        while not self._done:
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

    config_path = Path(__file__).parent.parent / "config.yaml"
    with config_path.open() as fp:
        _config = yaml.safe_load(fp)
        _config = Config.model_validate(_config)

    agent = CharacterCreationAgent(_config.agent)
    agent.run()
