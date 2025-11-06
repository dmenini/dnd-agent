from typing import Literal

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field

from agent.ai.components import create_llm
from agent.character.builder import CharacterBuilder
from agent.jobs.base import JobType
from agent.models.config import AgentConfig

DEFAULT_PARTY_NAME = "Players"


class CharacterCreationState(BaseModel):
    """State for dialogue-based multi-character creation."""

    messages: list[dict] = Field(default_factory=list)
    current_character: CharacterBuilder | None = None
    awaiting_continue_decision: bool = False
    done: bool = False
    characters: list[CharacterBuilder] = []
    party: str = DEFAULT_PARTY_NAME


class CharacterIntent(BaseModel):
    action: Literal["continue", "finalize"]
    message: str


class CharacterCreationAgent:
    """Handles natural dialogue flow for creating multiple characters."""

    def __init__(self, config: AgentConfig, max_players: int = 2) -> None:
        llm = create_llm(config.llm)
        self.mock_character = config.mock_character
        self.max_players = max_players

        self.dialogue_llm = llm.with_structured_output(CharacterIntent)
        self.character_llm = llm.with_structured_output(CharacterBuilder)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", config.prompts.character_builder.format(dm=config.prompts.dm)),
                MessagesPlaceholder("messages"),
            ]
        )

    async def respond(self, state: CharacterCreationState) -> CharacterCreationState:
        """Handle one conversational step, delegating by state context."""
        if state.awaiting_continue_decision:
            return await self._handle_continue_decision(state)
        return await self._handle_character_dialogue(state)

    async def _handle_continue_decision(self, state: CharacterCreationState) -> CharacterCreationState:
        """Interpret the user's response after being asked to continue or stop."""
        messages = self.prompt.format_messages(messages=state.messages)

        intent = (
            CharacterIntent(action="finalize", message="Let's stop here.")
            if self.mock_character
            else await self.dialogue_llm.ainvoke(messages)  # type: ignore[assignment]
        )

        state.messages.append({"role": "assistant", "content": intent.message})

        if intent.action == "continue":
            # TODO: This may feel robotic. Rephrase with DM?
            # Reset conversation so that next summarization doesn't hallucinate, but provide context as system message
            context = "So far we created {len(state.characters)} characters:\n"
            for char in state.characters:
                context += f"\n- {char.name}: {char.summary}"
            state.messages = [
                {
                    "role": "system",
                    "content": f"{context}\n\nLet's create another member of your party. Any input for me?",
                }
            ]
            state.current_character = None
        else:
            state.done = True

        state.awaiting_continue_decision = False
        return state

    async def _handle_character_dialogue(self, state: CharacterCreationState) -> CharacterCreationState:
        """Run the main dialogue flow for character creation."""
        messages = self.prompt.format_messages(messages=state.messages)

        intent = (
            CharacterIntent(action="finalize", message="Let's build your first hero!")
            if self.mock_character
            else await self.dialogue_llm.ainvoke(messages)  # type: ignore[assignment]
        )

        # TODO: This message is not logged as it's followed by the continuation message right afterwards
        state.messages.append({"role": "assistant", "content": intent.message})

        if intent.action == "finalize":
            await self._finalize_character(state)

        return state

    async def _finalize_character(self, state: CharacterCreationState) -> None:
        """Finalize the current character and ask whether to create another."""
        # Summarize conversation but exclude system message containing previous context to reduce hallucinations
        conversation_summary = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in state.messages if msg["role"] != "system"]
        )
        finalize_prompt = f"Based on this conversation, create a complete character:\n{conversation_summary}"

        character = (
            CharacterBuilder(
                name=f"Hero {len(state.characters) + 1}",
                icon="🧝",
                job=JobType.MAGE,
                summary="The default Hero of our story.",
            )
            if self.mock_character
            else await self.character_llm.ainvoke(finalize_prompt)  # type: ignore[assignment]
        )

        state.current_character = character
        state.characters.append(character)

        if len(state.characters) < self.max_players:
            continuation_prompt = (
                f"You now have {len(state.characters)} character(s) in your party. "
                f"Would you like to create another one?"
            )
            state.messages.append({"role": "assistant", "content": continuation_prompt})
            state.awaiting_continue_decision = True
        else:
            state.awaiting_continue_decision = False
            state.done = True
