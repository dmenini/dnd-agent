import pytest

from agent.character.abilities import AbilityType
from agent.character.character import Character
from agent.effects.status_effects.base import StatusType
from agent.effects.status_effects.collection import Paralyzed
from agent.equipment.weapons import MeleeWeapon, WeaponType
from agent.models.config import AgentConfig
from agent.models.damage import DamageType
from agent.models.decision import DecisionResult
from agent.models.enums import TargetingType
from agent.models.map import GameMap
from agent.models.state import State
from tests.conftest import advance_turn, cheater_dice


@pytest.mark.asyncio
async def test_paralyzed(config: AgentConfig, game_map: GameMap, actor: Character, target: Character) -> None:
    hero_id = actor.id
    orc_id = target.id

    sword = MeleeWeapon(
        name="Sword",
        damage_dice="2d6",
        damage_type=DamageType.SLASHING,
        weapon_type=WeaponType.MARTIAL_MELEE,
        targeting=TargetingType.SINGLE,
        effects=[Paralyzed.with_duration(duration=2)],
    )
    actor.equipment.main_hand = sword

    # Give target enough HP to survive both attacks
    # First attack: 15 damage, Second attack (crit): 25 damage = 40 total
    target.level = 10  # Higher level for more HP (should be > 40)
    starting_hp = target.max_hp
    target.attributes.hp = starting_hp

    state = State(
        map=game_map,
        characters={actor.id: actor, target.id: target},
        parties={actor.party.id: actor.party, target.party.id: target.party},
        turn_order=[hero_id, orc_id],
    )

    # Set deterministic rolls (value=5 to avoid crits on first hit)
    # 2d6=10 + STR mod (+5) = 15 damage
    actor.cheater_dice = cheater_dice(value=5)

    # Turn 1.1: Hero attacks and applies paralysis (damage=15)
    state = await advance_turn(
        state, result=DecisionResult(action_id="main_hand_attack", target_hits={orc_id: 1}, description="")
    )
    orc = state.characters[orc_id]
    assert orc.attributes.hp == starting_hp - 15
    assert orc.status_effects[0].type == StatusType.PARALYZED
    assert orc.status_effects[0].duration == 2
    assert orc.attributes.get_modifiers("advantage.defense")[0].value is True
    assert orc.attributes.get_modifiers("save_autofail.strength")[0].value is True
    assert orc.attributes.get_modifiers("save_autofail.dexterity")[0].value is True

    assert orc.attributes.advantage("defense") == 1
    assert orc.attributes.save_autofail(AbilityType.STR) is True
    assert orc.attributes.save_autofail(AbilityType.DEX) is True

    state = await advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 1.2: Orc paralyzed -> skip turn
    state = await advance_turn(state, result=DecisionResult(action_id="wait", description=""))
    assert state.action is None
    assert state.decision is None

    orc = state.characters[orc_id]
    assert orc.status_effects[0].type == StatusType.PARALYZED
    assert orc.status_effects[0].duration == 1

    # Turn 2.1: Hero attacks -> crit (paralyzed targets auto-crit in melee)
    # Critical damage = 4d6 (doubled dice) + STR mod = 20 + 5 = 25
    state = await advance_turn(
        state, result=DecisionResult(action_id="main_hand_attack", target_hits={orc_id: 1}, description="")
    )
    orc = state.characters[orc_id]
    assert orc.attributes.hp == starting_hp - 15 - 25  # First hit + crit

    state = await advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 2.2: Orc still paralyzed -> skip turn
    state = await advance_turn(state, result=DecisionResult(action_id="wait", description=""))
    assert state.action is None
    assert state.decision is None

    # Paralysis expires after 2 turns
    assert state.current_actor is not None
    orc = state.current_actor
    assert len(orc.status_effects) == 0
    assert orc.attributes.get_modifiers("defense_advantage") == []
    assert orc.attributes.get_modifiers("save_autofail.strength") == []
    assert orc.attributes.get_modifiers("save_autofail.dexterity") == []
