from typing import Literal

from anthropic import BaseModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import Field

from agent.ai.components import create_llm
from agent.character.builder import CharacterBuilder
from agent.models.config import AgentConfig


class CharacterCreationState(BaseModel):
    """State for character creation dialogue."""

    messages: list[dict] = Field(default_factory=list)
    character: CharacterBuilder | None = None
    done: bool = False


class CharacterIntent(BaseModel):
    action: Literal["continue", "finalize"]
    message: str


class CharacterCreationAgent:
    """Simple agent for character creation dialogue."""

    def __init__(self, config: AgentConfig) -> None:
        llm = create_llm(config.llm)
        self.controller_llm = llm.with_structured_output(CharacterIntent)
        self.character_llm = llm.with_structured_output(CharacterBuilder)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", config.prompts.character_builder.format(dm=config.prompts.dm)),
                MessagesPlaceholder("messages"),
            ]
        )

    async def respond(self, state: CharacterCreationState) -> CharacterCreationState:
        """Generate DM response and optionally finalize character."""
        # Get DM's response and intent
        messages = self.prompt.format_messages(messages=state.messages)
        intent = await self.controller_llm.ainvoke(messages)

        if not isinstance(intent, CharacterIntent):
            raise TypeError

        # Add DM's message to history
        state.messages.append({"role": "assistant", "content": intent.message})

        if intent.action == "finalize":
            # Generate final structured character from conversation
            conversation_summary = "\n".join([f"{msg['role']}: {msg['content']}" for msg in state.messages])

            finalize_prompt = f"""Based on this conversation, create a complete character:\n{conversation_summary}"""

            char = await self.character_llm.ainvoke(finalize_prompt)
            if not isinstance(char, CharacterBuilder):
                raise TypeError

            state.character = char
            state.done = True

        return state
