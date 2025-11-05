from pydantic import BaseModel


class ToolsConfig(BaseModel):
    pass


class LLMConfig(BaseModel):
    name: str
    temperature: float


class PromptsConfig(BaseModel):
    npc: str
    map: str
    dm: str
    character_builder: str


class AgentConfig(BaseModel):
    retries: int
    llm: LLMConfig
    prompts: PromptsConfig
    decision_node: dict = {}


class Config(BaseModel):
    agent: AgentConfig
    generate_map: bool = False
