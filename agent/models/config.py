from pydantic import BaseModel, Field


class ToolsConfig(BaseModel):
    pass


class LLMConfig(BaseModel):
    name: str
    temperature: float = 0.5


class PromptsConfig(BaseModel):
    npc: str
    map: str
    dm: str
    character_builder: str


class AgentConfig(BaseModel):
    mock_character: bool = False
    retries: int = 3
    llm: LLMConfig
    prompts: PromptsConfig
    decision_node: dict = Field(default_factory=dict)


class Config(BaseModel):
    agent: AgentConfig
    generate_map: bool = False
    map_size: tuple[int, int] = (12, 8)
    max_players: int = 2
