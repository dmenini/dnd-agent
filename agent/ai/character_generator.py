from pathlib import Path
from typing import Literal

import yaml
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda
from pydantic import BaseModel

from agent.ai.components import create_llm
from agent.character.builder import CharacterBuilder
from agent.models.config import AgentConfig, Config


class CharacterIntent(BaseModel):
    action: Literal["continue", "finalize"]
    message: str


def build_character_generator(config: AgentConfig) -> Runnable:
    # Base conversational LLM
    llm = create_llm(config.llm)

    # The LLM that can decide whether to continue or finalize
    controller_llm = llm.with_structured_output(CharacterIntent)

    # The LLM that generates the final structured character
    character_llm = llm.with_structured_output(CharacterBuilder)

    # Prompt for each conversational turn
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", config.prompts.character_builder.format(dm=config.prompts.dm)),
            ("user", "{input}"),
        ]
    )

    def agent_loop(user_input: str, memory: list[str]) -> CharacterBuilder | str:
        """Main agent loop."""
        while True:
            # Build input prompt with conversation context
            context = "\n".join(memory)
            messages = prompt.format_messages(input=f"{context}\nUser: {user_input}")

            # Ask the controller what to do
            intent = controller_llm.invoke(messages)
            memory.append(f"DM: {intent.message}")

            if intent.action == "finalize":
                # Generate final structured character
                summary = "\n".join(memory)
                return character_llm.invoke(f"Summarize and structure this character:\n{summary}")
            # Continue conversation
            print(intent.message)
            user_input = input("> ")  # (or handle through UI)
            memory.append(f"User: {user_input}")

    return RunnableLambda(lambda x: agent_loop(x["input"], []))


if __name__ == "__main__":
    config_path = Path(__file__).parent.parent / "config.yaml"
    with config_path.open() as fp:
        config = yaml.safe_load(fp)
        config = Config.model_validate(config)

    gen = build_character_generator(config.agent)
    result = gen.invoke({"input": "I'd like to create a tiefling bard who grew up in a circus."})
    print(result)
