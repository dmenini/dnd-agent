import pytest

from agent.character.abilities import AbilityType
from agent.character.character import Character
from agent.effects.status_effects.base import StatusType
from agent.jobs.wizard import Wizard
from agent.models.config import AgentConfig
from agent.models.decision import DecisionResult
from agent.models.enums import FeatureId
from agent.models.map import GameMap
from agent.models.state import State
from agent.services.job_service import JobService
from agent.services.level_service import LevelService
from tests.conftest import advance_turn, cheater_dice


@pytest.mark.asyncio
async def test_hasted(config: AgentConfig, game_map: GameMap, actor: Character, target: Character) -> None:
    actor.cheater_dice = None
    JobService.change_job(actor, Wizard)
    # Level up to 5 for 3rd level spell slots
    LevelService.level_up(actor)  # Level 4
    LevelService.level_up(actor)  # Level 5
    hero_id = actor.id
    orc_id = target.id

    state = State(
        map=game_map,
        characters={actor.id: actor, target.id: target},
        parties={actor.party.id: actor.party, target.party.id: target.party},
        turn_order=[hero_id, orc_id],
    )

    # Turn 1.1: Hero casts Haste on self
    state = await advance_turn(
        state, result=DecisionResult(action_id=FeatureId.HASTE.value, target_hits={hero_id: 1}, description="")
    )
    hero = state.characters[hero_id]
    assert hero.status_effects[0].type == StatusType.HASTED
    assert hero.status_effects[0].duration == 10

    ac_mods = hero.attributes.get_modifiers("ac")
    assert len(ac_mods) == 2
    assert ac_mods[0].value == 3
    assert ac_mods[1].value == 2

    assert hero.attributes.get_modifiers("speed")[0].value == 2
    assert hero.attributes.get_modifiers("save_advantage.dexterity")[0].value is True

    assert hero.armor_class == 15
    assert hero.current_speed == 12.0
    assert hero.attributes.ability_save_advantage(AbilityType.DEX) == 1

    state = await advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 1.2: Orc pass
    state = await advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 2.1: Hero can take multiple actions thanks to Haste
    assert state.current_actor is not None
    assert state.current_actor.status_effects[0].type == StatusType.HASTED
    assert state.current_actor.status_effects[0].duration == 10

    # Verify extra action from Haste allows double attack
    state = await advance_turn(
        state, result=DecisionResult(action_id="main_hand_attack", target_hits={orc_id: 1}, description="")
    )
    # Second attack in same turn thanks to Haste
    state = await advance_turn(
        state, result=DecisionResult(action_id="main_hand_attack", target_hits={orc_id: 1}, description="")
    )

    # Haste is still active
    hero = state.characters[hero_id]
    assert hero.status_effects[0].type == StatusType.HASTED

    # Advance enough turns for Haste to expire naturally (duration 10)
    # Set hero to fail WIS save (value=1) so Lethargic is applied when Haste expires
    hero = state.characters[hero_id]
    hero.cheater_dice = cheater_dice(value=1)

    # Skip ahead by passing for remaining turns (10 more rounds needed: current duration is 9 after Turn 2.1 ends)
    for _ in range(20):  # 10 rounds * 2 characters = 20 turns
        state = await advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Haste should have expired and Lethargic should be applied
    hero = state.characters[hero_id]
    assert len(hero.status_effects) == 1
    assert hero.status_effects[0].type == StatusType.LETHARGIC
    assert hero.status_effects[0].duration == 1
    assert hero.attributes.get_modifiers("speed")[0].value == 0.5
    assert hero.attributes.get_modifiers("save_disadvantage.wisdom")[0].value is True
    assert hero.attributes.speed() == 3.0  # Base 6 * 0.5 = 3.0
    assert hero.attributes.ability_save_advantage(AbilityType.WIS) == -1

    # Advance one more turn for Lethargic to expire
    state = await advance_turn(state, result=DecisionResult(action_id="wait", description=""))
    state = await advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Both effects should be gone now
    hero = state.characters[hero_id]
    assert len(hero.status_effects) == 0
