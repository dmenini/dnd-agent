from unittest.mock import MagicMock

import pytest
from langchain_core.language_models import BaseChatModel
from pytest_mock import MockerFixture

from agent.character.character import Character, Party
from agent.models.config import AgentConfig, LLMConfig, PromptsConfig
from agent.models.context import CombatContext
from agent.models.position import Position
from agent.models.state import DecisionResult, State
from agent.nodes.combat_engine import CombatEngineNode
from agent.nodes.decision import DecisionNode
from agent.nodes.end_combat import EndCombatNode
from agent.registration import register_actions, register_traits

register_actions()
register_traits()


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
    llm = mocker.MagicMock(spec=BaseChatModel)
    llm.with_structured_output.return_value = llm
    return llm


@pytest.fixture
def context() -> CombatContext:
    ctx = CombatContext()
    ctx.damage = None
    ctx.is_critical = False
    ctx.vulnerabilities = []
    return ctx


@pytest.fixture
def actor() -> Character:
    party_players = Party(id="p1", name="Heroes", is_player_party=True)
    return Character(
        id="hero",
        name="Alfred",
        icon="⚔️",
        pos=Position(x=2, y=2),
        is_player=True,
        party=party_players,
    )


@pytest.fixture
def target() -> Character:
    party_players = Party(id="p2", name="Monsters", is_player_party=True)
    return Character(
        id="orc",
        name="Orc",
        icon="👹",
        pos=Position(x=3, y=2),
        is_player=True,
        party=party_players,
    )


def advance_turn(state: State, result: DecisionResult) -> State:
    llm = MagicMock(spec=BaseChatModel)
    llm.with_structured_output.return_value = llm
    llm.invoke.return_value = result

    state = DecisionNode(llm=llm, system_prompt="")(state)
    state = CombatEngineNode()(state)
    return EndCombatNode()(state)
