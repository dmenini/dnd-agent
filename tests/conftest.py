from unittest.mock import AsyncMock

import pytest
from langchain_core.language_models import BaseChatModel
from pytest_mock import MockerFixture

from agent.ai.character_generator import DEFAULT_PARTY_NAME
from agent.character.abilities import AbilityType
from agent.character.attributes import Attributes
from agent.character.character import Character, Party
from agent.equipment.armor import Armor, ArmorType
from agent.equipment.weapons import MeleeWeapon, RangedWeapon, WeaponHandling, WeaponType
from agent.jobs.fighter import Fighter
from agent.jobs.wizard import Wizard
from agent.models.config import AgentConfig, LLMConfig, PromptsConfig
from agent.models.context import CombatContext
from agent.models.damage import DamageType
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


dagger = MeleeWeapon(
    name="Dagger",
    weapon_type=WeaponType.SIMPLE_MELEE,
    handling=WeaponHandling.ONE_HANDED,
    ability=AbilityType.DEX,
    damage_dice="1d4",
    damage_type=DamageType.PIERCING,
    finesse=True,
    dual_wield=True,
)

longsword = MeleeWeapon(
    name="Longsword",
    weapon_type=WeaponType.MARTIAL_MELEE,
    handling=WeaponHandling.VERSATILE,
    ability=AbilityType.STR,
    damage_dice="1d8",
    versatile_damage="1d10",
    damage_type=DamageType.SLASHING,
)

greatsword = MeleeWeapon(
    name="Greatsword",
    weapon_type=WeaponType.MARTIAL_MELEE,
    handling=WeaponHandling.TWO_HANDED,
    ability=AbilityType.STR,
    damage_dice="2d6",
    damage_type=DamageType.SLASHING,
)

bow = RangedWeapon(
    name="Bow",
    weapon_type=WeaponType.SIMPLE_RANGED,
    damage_type=DamageType.PIERCING,
    damage_dice="1d20",
    handling=WeaponHandling.ONE_HANDED,
)


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
    party_players = Party(id="p1", name=DEFAULT_PARTY_NAME, is_player_party=True)
    char = Character(
        id="alfred",
        name="Alfred",
        icon="⚔️",
        job=Fighter,
        level=3,
        pos=Position(x=2, y=2),
        attributes=Attributes(strength=20, primary_ability=AbilityType.STR),
        is_player=True,
        party=party_players,
    )
    char.attributes.hp = 15
    return char


@pytest.fixture
def target() -> Character:
    party_players = Party(id="p2", name="Monsters", is_player_party=True)
    char = Character(
        id="orc",
        name="Orc",
        icon="👹",
        job=Wizard,
        level=3,
        pos=Position(x=3, y=2),
        party=party_players,
        armor=Armor(
            name="Armor",
            description="",
            armor_type=ArmorType.HEAVY,
            base_ac=0,
        ),
    )
    char.attributes.hp = 15
    return char


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
