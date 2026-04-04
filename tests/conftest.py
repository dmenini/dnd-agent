from unittest.mock import AsyncMock

import pytest
from langchain_core.language_models import BaseChatModel
from pytest_mock import MockerFixture

from agent.ai.character_creation.agent import DEFAULT_PARTY_NAME
from agent.character.abilities import AbilityType
from agent.character.attributes import Attributes
from agent.character.character import Character, Party
from agent.character.combat_stats import CombatStats
from agent.character.equipment import Equipment
from agent.effects.trait_effects.damage import *  # noqa: F403
from agent.effects.trait_effects.support import *  # noqa: F403
from agent.effects.trait_effects.turn import *  # noqa: F403
from agent.equipment.armor import Armor, ArmorType
from agent.equipment.weapons import MeleeWeapon, RangedWeapon, WeaponHandling, WeaponType
from agent.jobs.cleric import Cleric
from agent.jobs.fighter import Fighter
from agent.jobs.wizard import Wizard
from agent.mechanics.dice_roller import DiceRoller
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
from agent.registration import register_actions

register_actions()

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
        combat=CombatStats(pos=Position(x=2, y=2)),
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
        combat=CombatStats(pos=Position(x=3, y=2)),
        party=party_players,
        equipment=Equipment(
            armor=Armor(
                name="Armor",
                description="",
                armor_type=ArmorType.HEAVY,
                base_ac=0,
            )
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
        characters={actor.id: actor.combat.pos, target.id: target.combat.pos},
        icons={actor.id: actor.icon, target.id: target.icon},
    )


@pytest.fixture
def fighter() -> Character:
    """A fighter character for testing."""
    party = Party(id="p1", name="Heroes", is_player_party=True)
    char = Character(
        id="fighter",
        name="Fighter",
        icon="⚔️",
        job=Fighter,
        level=5,
        pos=Position(x=0, y=0),
        attributes=Attributes(
            strength=16,
            dexterity=14,
            constitution=15,
            intelligence=10,
            wisdom=12,
            charisma=8,
            primary_ability=AbilityType.STR,
        ),
        is_player=True,
        party=party,
    )
    char.attributes.hp = 45
    char.attributes.base_hp = 45
    char.attributes.base_speed = 6
    return char


@pytest.fixture
def orc() -> Character:
    """An orc enemy for testing."""
    party = Party(id="p2", name="Monsters", is_player_party=False)
    char = Character(
        id="orc",
        name="Orc",
        icon="👹",
        job=Fighter,  # Generic enemy
        level=3,
        pos=Position(x=5, y=0),
        attributes=Attributes(
            strength=16,
            dexterity=12,
            constitution=16,
            intelligence=7,
            wisdom=11,
            charisma=10,
            primary_ability=AbilityType.STR,
        ),
        party=party,
    )
    char.attributes.hp = 30
    char.attributes.base_hp = 30
    char.attributes.base_ac = 13
    return char


@pytest.fixture
def wizard() -> Character:
    """A wizard character for testing."""
    party = Party(id="p1", name="Heroes", is_player_party=True)
    char = Character(
        id="wizard",
        name="Wizard",
        icon="🧙",
        job=Wizard,
        level=5,
        pos=Position(x=0, y=0),
        attributes=Attributes(
            strength=8,
            dexterity=14,
            constitution=13,
            intelligence=17,
            wisdom=12,
            charisma=10,
            primary_ability=AbilityType.INT,
            spellcasting_ability=AbilityType.INT,
        ),
        is_player=True,
        party=party,
    )
    char.attributes.hp = 28
    char.attributes.base_hp = 28
    return char


@pytest.fixture
def cleric() -> Character:
    """A cleric character for testing."""
    party = Party(id="p1", name="Heroes", is_player_party=True)
    char = Character(
        id="cleric",
        name="Cleric",
        icon="✝️",
        job=Cleric,
        level=5,
        pos=Position(x=0, y=0),
        attributes=Attributes(
            strength=14,
            dexterity=10,
            constitution=14,
            intelligence=10,
            wisdom=17,
            charisma=13,
            primary_ability=AbilityType.WIS,
            spellcasting_ability=AbilityType.WIS,
        ),
        is_player=True,
        party=party,
    )
    char.attributes.hp = 38
    char.attributes.base_hp = 38
    return char


async def advance_turn(state: State, result: DecisionResult) -> State:
    llm = AsyncMock(spec=BaseChatModel)
    llm.with_structured_output.return_value = llm
    llm.ainvoke.return_value = result

    state = await StartCombatNode()(state)
    state = await DecisionNode(llm=llm, system_prompt="", simulation=True)(state)
    state = await ActionProcessorNode()(state)
    return await EndCombatNode()(state)


@pytest.fixture
def char_creation_config() -> AgentConfig:
    """Config for character creation testing."""
    return AgentConfig(
        llm=LLMConfig(name="fake", temperature=0),
        prompts=PromptsConfig(npc="", map="", dm="Test DM", character_builder="Test builder. {dm}"),
        retries=1,
        mock_character=False,
    )


@pytest.fixture
def mock_tool_runtime(mocker: MockerFixture):  # type: ignore[no-untyped-def]  # noqa: ANN201
    """Factory for creating mock ToolRuntime objects."""
    from langgraph.prebuilt import ToolRuntime  # noqa: PLC0415

    def _create(state_data: dict):  # type: ignore[no-untyped-def]  # noqa: ANN202
        config = mocker.MagicMock()
        stream_writer = mocker.MagicMock()
        return ToolRuntime(
            state=state_data,
            context=None,
            config=config,
            stream_writer=stream_writer,
            tool_call_id="test_call_123",
            store=None,
        )

    return _create


def cheater_dice(value: int = 10) -> DiceRoller:
    """Factory for creating deterministic dice rollers for testing.

    Usage:
        def test_something(actor, cheater_dice):
            actor.cheater_dice = cheater_dice(value=15)
            # Now all rolls for this actor will return 15
    """

    return DiceRoller(value=value)
