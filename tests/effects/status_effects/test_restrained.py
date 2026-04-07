import pytest

from agent.character.abilities import AbilityType
from agent.character.character import Character
from agent.effects.status_effects.base import StatusType
from agent.effects.status_effects.collection import Restrained
from agent.equipment.weapons import MeleeWeapon, WeaponType
from agent.models.config import AgentConfig
from agent.models.damage import DamageType
from agent.models.decision import DecisionResult
from agent.models.enums import TargetingType
from agent.models.map import GameMap
from agent.models.state import State
from tests.conftest import advance_turn, cheater_dice


@pytest.mark.asyncio
async def test_restrained(config: AgentConfig, game_map: GameMap, actor: Character, target: Character) -> None:
    hero_id = actor.id
    enemy_id = target.id

    sword = MeleeWeapon(
        name="Sword",
        damage_dice="2d6",
        damage_type=DamageType.SLASHING,
        weapon_type=WeaponType.MARTIAL_MELEE,
        targeting=TargetingType.SINGLE,
        effects=[Restrained.with_duration(2)],
    )
    actor.equipment.main_hand = sword

    # Give target more HP to survive the attack
    target.level = 5  # Higher level means more HP
    starting_hp = target.max_hp
    target.attributes.hp = starting_hp

    state = State(
        map=game_map,
        characters={actor.id: actor, target.id: target},
        parties={actor.party.id: actor.party, target.party.id: target.party},
        turn_order=[hero_id, enemy_id],
    )

    # Set deterministic rolls (value=5 for d20 and damage dice)
    # d20=5 won't crit, 2d6=5+5=10 + STR modifier (+5) = 15 damage
    actor.cheater_dice = cheater_dice(value=5)

    # Turn 1.1: Hero attacks and applies restrained (damage=15)
    state = await advance_turn(
        state, result=DecisionResult(action_id="main_hand_attack", target_hits={enemy_id: 1}, description="")
    )
    enemy = state.characters[enemy_id]
    assert target.attributes.hp == starting_hp - 15
    assert enemy.status_effects[0].type == StatusType.RESTRAINED
    assert enemy.status_effects[0].duration == 2
    assert enemy.attributes.get_modifiers("advantage.defense")[0].value is True
    assert enemy.attributes.get_modifiers("disadvantage.attack")[0].value is True
    assert enemy.attributes.get_modifiers("save_disadvantage.dexterity")[0].value is True
    assert enemy.attributes.advantage("defense") == 1
    assert enemy.attributes.advantage("attack") == -1
    assert enemy.attributes.ability_save_advantage(AbilityType.DEX) == -1

    state = await advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 1.2: Orc restrained -> after attack no more actions available and passes (no need to wait)
    state = await advance_turn(
        state, result=DecisionResult(action_id="main_hand_attack", target_hits={enemy_id: 1}, description="")
    )

    enemy = state.characters[enemy_id]
    assert enemy.status_effects[0].type == StatusType.RESTRAINED
    assert enemy.status_effects[0].duration == 1

    # Turn 2.1: Pass
    assert state.current_actor is not None
    assert state.current_actor.id == hero_id
    state = await advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 2.2: Enemy still restrained -> skip turn
    state = await advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Paralysis expires after 2 turns
    assert state.current_actor is not None
    enemy = state.current_actor
    assert len(enemy.status_effects) == 0
    assert enemy.attributes.get_modifiers("defense_advantage") == []
    assert enemy.attributes.get_modifiers("attack_advantage") == []
    assert enemy.attributes.get_modifiers("dex_save_advantage") == []
