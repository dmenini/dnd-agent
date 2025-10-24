from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from agent.ai.components import create_llm
from agent.models.config import AgentConfig
from agent.models.map import GameMap


def build_map_generator(config: AgentConfig) -> Runnable:
    prompt_template = ChatPromptTemplate.from_messages([("system", config.prompts.map), ("user", "{input}")])
    llm = create_llm(config.llm)
    llm = llm.with_structured_output(GameMap)  # type: ignore[assignment]
    return prompt_template | llm
