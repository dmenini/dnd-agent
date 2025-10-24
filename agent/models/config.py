from pydantic import BaseModel


class ToolsConfig(BaseModel):
    pass


class LLMConfig(BaseModel):
    name: str
    temperature: float


class PromptsConfig(BaseModel):
    system: str
    map: str


class AgentConfig(BaseModel):
    retries: int
    llm: LLMConfig
    prompts: PromptsConfig


class Config(BaseModel):
    agent: AgentConfig
