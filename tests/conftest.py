from unittest.mock import AsyncMock

import pytest
from langchain_core.language_models import BaseChatModel
from pytest_mock import MockerFixture

from agent.character.attributes import Attributes
from agent.character.character import Character, Party
from agent.equipment.armor import Armor, ArmorType
from agent.jobs.fighter import Fighter
from agent.jobs.mage import Mage
from agent.models.config import AgentConfig, LLMConfig, PromptsConfig
from agent.models.context import CombatContext
from agent.models.decision import DecisionResult
from agent.models.map import GameMap
from agent.models.position import Position
from agent.models.state import State
from agent.nodes.action_processor import ActionProcessorNode
from agent.nodes.decision import DecisionNode
from agent.nodes.end_combat import EndCombatNode
from agent.nodes.start_combat import StartCombatNode
from agent.registration import register_actions, register_traits

register_actions()
register_traits()


@pytest.fixture
def config() -> AgentConfig:
    """Mocked config with fake LLM setup."""
    return AgentConfig(
        llm=LLMConfig(name="fake", temperature=0),
        prompts=PromptsConfig(
            npc="You are a decision-making combat AI.", map="Generate the map", character_builder="", dm=""
        ),
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
        job=Fighter,
        pos=Position(x=2, y=2),
        attributes=Attributes(strength=20),
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
        job=Mage,
        pos=Position(x=3, y=2),
        party=party_players,
        armor=Armor(
            name="Armor",
            description="",
            armor_type=ArmorType.HEAVY,
            base_ac=0,
        ),
    )


@pytest.fixture
def game_map(actor: Character, target: Character) -> GameMap:
    return GameMap(
        map="",
        width=10,
        height=10,
        characters={actor.id: actor.pos, target.id: target.pos},
        icons={actor.id: actor.icon, target.id: target.icon},
    )


async def advance_turn(state: State, result: DecisionResult) -> State:
    llm = AsyncMock(spec=BaseChatModel)
    llm.with_structured_output.return_value = llm
    llm.ainvoke.return_value = result

    state = await StartCombatNode()(state)
    state = await DecisionNode(llm=llm, system_prompt="", simulation=True)(state)
    state = await ActionProcessorNode()(state)
    return await EndCombatNode()(state)
