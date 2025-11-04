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


def generate_game_map(chain: Runnable, enemies: list[str], players: list[str], map_size: tuple[int, int]) -> GameMap:
    user_template = f"These are the characters that take part in the combat:\nEnemies: {enemies}\nPlayers: {players}"
    game_map = chain.invoke(
        {
            "width": map_size[0],
            "height": map_size[1],
            "input": user_template,
        }
    )
    if not isinstance(game_map, GameMap):
        raise TypeError
    return game_map
