import pytest

from agent.character.character import Character
from agent.effects.status_effects.base import EffectType
from agent.equipment.weapons import MeleeWeapon, WeaponType
from agent.models.config import AgentConfig
from agent.models.damage import DamageType
from agent.models.decision import DecisionResult
from agent.models.enums import TargetingType
from agent.models.map import GameMap
from agent.models.state import State
from tests.conftest import advance_turn


@pytest.mark.asyncio
async def test_dodge(config: AgentConfig, game_map: GameMap, actor: Character, target: Character) -> None:
    hero_id = actor.id
    orc_id = target.id

    sword = MeleeWeapon(
        name="Sword",
        damage_dice="1d5",
        weapon_type=WeaponType.MARTIAL_MELEE,
        targeting=TargetingType.SINGLE,
        damage_type=DamageType.SLASHING,
    )
    actor.main_hand = sword

    state = State(
        map=game_map,
        characters={actor.id: actor, target.id: target},
        parties={actor.party.id: actor.party, target.party.id: target.party},
        turn_order=[hero_id, orc_id],
    )

    # Turn 1.1: Hero casts Haste on self
    state = await advance_turn(
        state, result=DecisionResult(action_id="dodge", target_hits={hero_id: 1}, description="")
    )
    hero = state.characters[hero_id]
    assert hero.status_effects[0].type == EffectType.DODGING
    assert hero.status_effects[0].duration == 1
    assert hero.attributes.get_modifiers("disadvantage.defense")[0].value is True

    assert hero.attributes.advantage("defense") == -1

    state = await advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 1.2: Orc pass
    state = await advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 2.1: Dodge expires
    assert state.current_actor is not None
    assert state.current_actor.status_effects[0].type == EffectType.DODGING
    assert state.current_actor.status_effects[0].duration == 1
    state = await advance_turn(state, result=DecisionResult(action_id="wait", description=""))
    assert state.current_actor is not None
    assert len(state.current_actor.status_effects) == 0
