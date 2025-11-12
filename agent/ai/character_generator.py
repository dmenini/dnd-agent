import uuid
from typing import TYPE_CHECKING

from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver

from agent.ai.components import create_llm
from agent.character.abilities import SkillType
from agent.character.builder import CharacterBuilder, CharacterSelections, options_map
from agent.equipment.base import EquipmentSlot
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
        self._done = False
        self._started = False

        # Track current character being built
        self._current_builder: CharacterBuilder | None = None

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
        def get_class_options_tool(job_type: JobType) -> str:
            """
            Get available options for a character class.
            Use this to show players what choices they have for skills, equipment, and features.

            Returns:
                Formatted string describing all available options
            """
            options = options_map.get(job_type)
            if not options:
                return f"No detailed options found for {job_type.value}"

            result = f"Options for {job_type.value}:\n\n"

            # Skills
            result += f"**Skills** (choose {options.skill_count}):\n"
            for skill in options.skill_choices:
                result += f"  - {skill.value}\n"

            # Equipment
            if options.equipment_choices:
                result += "\n**Equipment Choices**:\n"
                for eq_choice in options.equipment_choices:
                    result += f"  {eq_choice.slot.value} - {eq_choice.description}:\n"
                    for opt in eq_choice.options:
                        result += f"    - {opt}\n"

            # Features
            if options.feature_choices:
                result += "\n**Class Features**:\n"
                for feat_choice in options.feature_choices:
                    result += f"  {feat_choice.feature_name} - {feat_choice.description}:\n"
                    for opt in feat_choice.options:
                        result += f"    - {opt}\n"

            return result

        @tool
        def start_character_creation(character: CharacterBuilder) -> str:
            """
            Begin creating a new character with basic information.
            This initializes the character builder. After this, guide the player
            through selecting skills, equipment, and features.

            Returns:
                Next steps message
            """
            self._current_builder = character

            return (
                f"Started creating {character.name}, the {character.job.value}! "
                f"Now let's choose their skills, equipment, and features. "
                f"Use get_class_options_tool to see what's available."
            )

        @tool
        def set_skill_proficiencies(skills: list[SkillType]) -> str:
            """
            Set the skill proficiencies for the character being created.
            Only call this after the player has selected from the valid options.

            Args:
                skills: List of skill names chosen by the player

            Returns:
                Confirmation message
            """
            if not self._current_builder:
                return "No character is currently being created. Use start_character_creation first."

            options = options_map.get(self._current_builder.job)
            if not options:
                return "Cannot set skills - no options available for this class."

            # Validate selections
            invalid = [s for s in skills if s not in options.skill_choices]

            if invalid:
                return f"Invalid skill choices: {invalid}. Valid options: {options.skill_choices}"

            if len(skills) > options.skill_count:
                return f"Must choose exactly {options.skill_count} skills. You chose {len(skills)}."

            # Convert to SkillType enums and store
            skill_enums = [SkillType(s) for s in skills]
            self._current_builder.selections.skill_proficiencies = skill_enums

            return "Success: skills set!"

        @tool
        def set_equipment_choice(slot: EquipmentSlot, choice: str) -> str:
            """
            Set an equipment choice for the character.

            Args:
                slot: Equipment slot identifier
                choice: The selected equipment option

            Returns:
                Confirmation message
            """
            if not self._current_builder:
                return "No character is currently being created. Use start_character_creation first."

            options = options_map.get(self._current_builder.job)
            if not options:
                return "No equipment options for this class."

            # Find the equipment choice
            eq_choice = next((e for e in options.equipment_choices if e.slot == slot), None)
            if not eq_choice:
                return f"Invalid equipment slot: {slot}"

            if choice not in eq_choice.options:
                return f"Invalid choice '{choice}' for {slot}. Options: {eq_choice.options}"

            self._current_builder.selections.equipment[slot] = choice
            return f"Success: slot {slot.value} set to {choice}"

        @tool
        def set_feature_choice(feature_name: str, choice: str) -> str:
            """
            Set a class feature choice.

            Args:
                feature_name: Name of the feature
                choice: The selected option

            Returns:
                Confirmation message
            """
            if not self._current_builder:
                return "No character is currently being created. Use start_character_creation first."

            options = options_map.get(self._current_builder.job)
            if not options:
                return "No feature options for this class."

            feat_choice = next((f for f in options.feature_choices if f.feature_name == feature_name), None)
            if not feat_choice:
                return f"Invalid feature: {feature_name}"

            # Check if choice matches any option (allow partial matching)
            matching_option = None
            for opt in feat_choice.options:
                if choice.lower() in opt.lower() or opt.lower().startswith(choice.lower()):
                    matching_option = opt
                    break

            if not matching_option:
                return f"Invalid choice for {feature_name}. Options: {feat_choice.options}"

            self._current_builder.selections.features[feature_name] = matching_option
            return f"Success: feature {feature_name} set to {matching_option}"

        @tool
        def finalize_character() -> str:
            """
            Call this after all mechanical choices (skills, equipment, features) are made.

            Returns:
                Confirmation message
            """
            if not self._current_builder:
                return "No character is currently being created."

            # Validate all required choices are made
            options = options_map.get(self._current_builder.job)
            if options:
                # Check skills
                if len(self._current_builder.selections.skill_proficiencies) != options.skill_count:
                    return f"Must choose {options.skill_count} skills before finalizing."

                # Check equipment
                missing_equipment = [
                    e.slot
                    for e in options.equipment_choices
                    if e.slot not in self._current_builder.selections.equipment
                ]
                if missing_equipment:
                    return f"Missing equipment choices: {missing_equipment}"

                # Check features
                missing_features = [
                    f.feature_name
                    for f in options.feature_choices
                    if f.feature_name not in self._current_builder.selections.features
                ]
                if missing_features:
                    return f"Missing feature choices: {missing_features}"

            # Save character
            self.characters.append(self._current_builder)
            msg = f"Character creation complete: {self._current_builder.name}"

            self._current_builder = None

            if len(self.characters) == self.max_players:
                self._done = True

            return msg

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

                if self._current_builder:
                    context += f"\n\nCurrently creating: {self._current_builder.name}"
                else:
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

            context = f"Party complete with {len(self.characters)}/{self.max_players} character(s):\n"
            for char in self.characters:
                context += f"\n- {char.name}: {char.summary}"
            return context

        return [
            get_class_options_tool,
            start_character_creation,
            set_skill_proficiencies,
            set_equipment_choice,
            set_feature_choice,
            finalize_character,
            get_party_status,
            finalize_party,
        ]

    def reset(self) -> None:
        self.characters = []
        self._current_builder = None
        self._thread_id = str(uuid.uuid4())
        self._done = False
        self._started = False

    def create_snapshot(self) -> dict:
        """Create a complete snapshot of the current state."""
        return {
            "characters": self.characters,
            "current_builder": self._current_builder,
            "thread_id": self._thread_id,
            "done": self._done,
            "started": self._started,
        }

    def load_snapshot(self, snapshot: dict) -> None:
        """Load a snapshot, restoring state."""
        self.characters = snapshot["characters"]
        self._current_builder = snapshot["current_builder"]
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
                selections=CharacterSelections(skill_proficiencies=[SkillType.ARCANA, SkillType.HISTORY]),
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
