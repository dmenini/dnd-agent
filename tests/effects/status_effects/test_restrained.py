from unittest.mock import MagicMock

from agent.character.character import Character
from agent.character.stats import StatType
from agent.effects.status_effects.base import EffectType
from agent.effects.status_effects.restrained import Restrained
from agent.equipment.weapons import MeleeWeapon, WeaponType
from agent.mechanics.dice_roller import DiceRoll
from agent.models.config import AgentConfig
from agent.models.damage import DamageType
from agent.models.decision import DecisionResult
from agent.models.enums import TargetingType
from agent.models.map import GameMap
from agent.models.state import State
from tests.conftest import advance_turn


def test_restrained(config: AgentConfig, game_map: GameMap, actor: Character, target: Character) -> None:
    hero_id = actor.id
    orc_id = target.id

    sword = MeleeWeapon(
        name="Sword",
        damage_dice="2d6",
        damage_type=DamageType.SLASHING,
        weapon_type=WeaponType.MARTIAL_MELEE,
        targeting=TargetingType.SINGLE,
        effects=[Restrained(duration=2)],
    )
    actor.main_hand = sword

    starting_hp = 20
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

    # Turn 1.1: Hero attacks and applies restrained
    state = advance_turn(
        state, result=DecisionResult(action_id="main_hand_attack", target_hits={orc_id: 1}, description="")
    )
    orc = state.characters[orc_id]
    assert orc.attributes.hp == starting_hp - value1
    assert orc.status_effects[0].type == EffectType.RESTRAINED
    assert orc.status_effects[0].duration == 2
    assert orc.attributes.get_modifiers("advantage.defense")[0].value is True
    assert orc.attributes.get_modifiers("disadvantage.attack")[0].value is True
    assert orc.attributes.get_modifiers("save_disadvantage.dex")[0].value is True
    assert orc.attributes.advantage("defense") == 1
    assert orc.attributes.advantage("attack") == -1
    assert orc.attributes.stat_save_advantage(StatType.DEX) == -1

    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 1.2: Orc restrained -> after attack no more actions available and passes (no need to wait)
    state = advance_turn(
        state, result=DecisionResult(action_id="main_hand_attack", target_hits={orc_id: 1}, description="")
    )

    orc = state.characters[orc_id]
    assert orc.status_effects[0].type == EffectType.RESTRAINED
    assert orc.status_effects[0].duration == 1

    # Turn 2.1: Pass
    assert state.current_actor.id == hero_id
    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 2.2: Orc still restrained -> skip turn
    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Paralysis expires after 2 turns
    orc = state.current_actor
    assert len(orc.status_effects) == 0
    assert orc.attributes.get_modifiers("defense_advantage") == []
    assert orc.attributes.get_modifiers("attack_advantage") == []
    assert orc.attributes.get_modifiers("dex_save_advantage") == []
