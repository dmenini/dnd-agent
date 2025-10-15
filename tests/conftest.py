from unittest.mock import MagicMock

import pytest
from langchain_core.language_models import BaseChatModel
from pytest_mock import MockerFixture

from agent.models.config import AgentConfig, LLMConfig, PromptsConfig
from agent.models.state import DecisionResult, State
from agent.nodes.combat_engine import CombatEngineNode
from agent.nodes.decision import DecisionNode
from agent.nodes.end_combat import EndCombatNode


@pytest.fixture
def config() -> AgentConfig:
    """Mocked config with fake LLM setup."""
    return AgentConfig(
        llm=LLMConfig(name="fake", temperature=0),
        prompts=PromptsConfig(system="You are a decision-making combat AI."),
        retries=1,
    )


@pytest.fixture
def fake_llm(mocker: MockerFixture) -> BaseChatModel:
    """A fake LLM that always returns a fixed decision."""
    llm = mocker.MagicMock(stub=BaseChatModel)
    llm.with_structured_output.return_value = llm
    return llm


def advance_turn(state: State, result: DecisionResult) -> State:
    llm = MagicMock(stub=BaseChatModel)
    llm.with_structured_output.return_value = llm
    llm.invoke.return_value = result

    state = DecisionNode(llm=llm, system_prompt="")(state)
    state = CombatEngineNode()(state)
    return EndCombatNode()(state)
