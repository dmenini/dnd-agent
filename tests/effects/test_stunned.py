from unittest.mock import MagicMock

from agent.character.attributes import Attributes
from agent.character.character import Character, Party
from agent.character.stats import StatType
from agent.effects.base import EffectType
from agent.effects.stunned import Stunned
from agent.equipment.weapons import MeleeWeapon, WeaponType
from agent.mechanics.dice_roller import DiceRoll
from agent.models.config import AgentConfig
from agent.models.damage import DamageType
from agent.models.enums import TargetingType
from agent.models.position import Position
from agent.models.state import DecisionResult, State
from tests.conftest import advance_turn


def test_stunned(
    config: AgentConfig,
) -> None:
    hero_id = "hero"
    orc_id = "orc"

    party_players = Party(id="p1", name="Heroes", is_player_party=True)
    party_enemies = Party(id="p2", name="Enemies", is_player_party=False)

    sword = MeleeWeapon(
        name="Sword",
        damage_dice="2d6",
        damage_type=DamageType.SLASHING,
        weapon_type=WeaponType.MARTIAL_MELEE,
        range=2,
        targeting=TargetingType.SINGLE,
        effects=[Stunned(duration=2)],
    )
    hero = Character(
        id=hero_id,
        name="Alfred",
        icon="⚔️",
        pos=Position(x=2, y=2),
        is_player=True,
        party=party_players,
        main_hand=sword,
    )
    orc = Character(
        id=orc_id,
        name="Orc Grunt",
        icon="👹",
        pos=Position(x=4, y=2),
        attributes=Attributes(hp=20),
        party=party_enemies,
    )

    state = State(
        characters={hero.id: hero, orc.id: orc},
        parties={party_players.id: party_players, party_enemies.id: party_enemies},
        turn_order=[hero_id, orc_id],
    )

    hero._dice = MagicMock()
    value1 = 15
    hero._dice.roll_with_context.return_value = DiceRoll(expression="1d20", rolls=[], total=value1, raw=value1)
    orc._dice = MagicMock()
    orc._dice.roll_with_context.return_value = DiceRoll(expression="1d20", rolls=[], total=1, raw=1)

    # Turn 1.1: Hero attacks and applies stun
    state = advance_turn(
        state, result=DecisionResult(action_id="main_hand_attack", target_ids=[orc_id], description="")
    )
    orc = state.characters[orc_id]
    assert orc.status_effects[0].type == EffectType.STUNNED
    assert orc.status_effects[0].duration == 2
    assert orc.attributes.get_modifiers("advantage.defense")[0].value == 1
    assert orc.attributes.get_modifiers("save_autofail.str")[0].value is True
    assert orc.attributes.get_modifiers("save_autofail.dex")[0].value is True

    assert orc.attributes.advantage("defense") == 1
    assert orc.attributes.save_autofail(StatType.STR) is True
    assert orc.attributes.save_autofail(StatType.DEX) is True

    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 1.2: Orc stunned -> skip turn
    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))
    assert state.action is None
    assert state.decision is None

    orc = state.characters[orc_id]
    assert orc.status_effects[0].type == EffectType.STUNNED
    assert orc.status_effects[0].duration == 1

    # Turn 2.1: Pass
    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 2.2: Orc still stunned -> skip turn
    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))
    assert state.action is None
    assert state.decision is None

    # Stunned expires after 2 turns
    orc = state.current_actor
    assert len(orc.status_effects) == 0
    assert orc.attributes.get_modifiers("advantage.defense") == []
    assert orc.attributes.get_modifiers("save_autofail.str") == []
    assert orc.attributes.get_modifiers("save_autofail.dec") == []
