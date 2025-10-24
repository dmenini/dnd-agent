from langchain_aws import ChatBedrockConverse
from langchain_core.language_models import BaseChatModel

from agent.models.config import LLMConfig


def create_llm(config: LLMConfig) -> BaseChatModel:
    # Converse API: https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html
    return ChatBedrockConverse(
        model=config.name,
        temperature=config.temperature,
    )
