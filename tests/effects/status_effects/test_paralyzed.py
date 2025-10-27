from unittest.mock import MagicMock

from agent.character.character import Character
from agent.character.stats import StatType
from agent.effects.status_effects.base import EffectType
from agent.effects.status_effects.paralyzed import Paralyzed
from agent.equipment.weapons import MeleeWeapon, WeaponType
from agent.mechanics.dice_roller import DiceRoll
from agent.models.config import AgentConfig
from agent.models.damage import DamageType
from agent.models.decision import DecisionResult
from agent.models.enums import TargetingType
from agent.models.map import GameMap
from agent.models.state import State
from tests.conftest import advance_turn


def test_paralyzed(config: AgentConfig, game_map: GameMap, actor: Character, target: Character) -> None:
    hero_id = actor.id
    orc_id = target.id

    sword = MeleeWeapon(
        name="Sword",
        damage_dice="2d6",
        damage_type=DamageType.SLASHING,
        weapon_type=WeaponType.MARTIAL_MELEE,
        targeting=TargetingType.SINGLE,
        effects=[Paralyzed(duration=2)],
    )
    actor.main_hand = sword

    starting_hp = 30
    target.attributes.hp = starting_hp

    state = State(
        map=game_map,
        characters={actor.id: actor, target.id: target},
        parties={actor.party.id: actor.party, target.party.id: target.party},
        turn_order=[hero_id, orc_id],
    )

    actor._dice = MagicMock()
    value1 = 15
    actor._dice.roll_with_context.return_value = DiceRoll(expression="1d20", rolls=[], total=value1, raw=value1)
    actor._dice.roll_once.return_value = DiceRoll(expression="1d20", rolls=[], total=value1, raw=value1)
    actor._dice.roll_twice.return_value = DiceRoll(expression="2d20", rolls=[], total=value1 * 2, raw=value1)

    # Turn 1.1: Hero attacks and applies paralysis
    state = advance_turn(
        state, result=DecisionResult(action_id="main_hand_attack", target_hits={orc_id: 1}, description="")
    )
    orc = state.characters[orc_id]
    assert orc.attributes.hp == starting_hp - value1
    assert orc.status_effects[0].type == EffectType.PARALYZED
    assert orc.status_effects[0].duration == 2
    assert orc.attributes.get_modifiers("advantage.defense")[0].value is True
    assert orc.attributes.get_modifiers("save_autofail.str")[0].value is True
    assert orc.attributes.get_modifiers("save_autofail.dex")[0].value is True

    assert orc.attributes.advantage("defense") == 1
    assert orc.attributes.save_autofail(StatType.STR) is True
    assert orc.attributes.save_autofail(StatType.DEX) is True

    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 1.2: Orc paralyzed -> skip turn
    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))
    assert state.action is None
    assert state.decision is None

    orc = state.characters[orc_id]
    assert orc.status_effects[0].type == EffectType.PARALYZED
    assert orc.status_effects[0].duration == 1

    # Turn 2.1: Hero attacks -> crit
    actor._dice = MagicMock()
    value2 = 5
    actor._dice.roll_with_context.return_value = DiceRoll(expression="1d20", rolls=[], total=value2, raw=value2)
    actor._dice.roll_once.return_value = DiceRoll(expression="1d20", rolls=[], total=value2, raw=value2)
    actor._dice.roll_twice.return_value = DiceRoll(expression="2d20", rolls=[], total=value2 * 2, raw=value2)

    state = advance_turn(
        state, result=DecisionResult(action_id="main_hand_attack", target_hits={orc_id: 1}, description="")
    )
    crit_damage = value2 + value2
    assert orc.attributes.hp == starting_hp - value1 - crit_damage

    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 2.2: Orc still paralyzed -> skip turn
    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))
    assert state.action is None
    assert state.decision is None

    # Paralysis expires after 2 turns
    orc = state.current_actor
    assert len(orc.status_effects) == 0
    assert orc.attributes.get_modifiers("defense_advantage") == []
    assert orc.attributes.get_modifiers("str_save_autofail") == []
    assert orc.attributes.get_modifiers("dex_save_autofail") == []
