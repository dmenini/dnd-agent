# mypy: disable-error-code="union-attr"
from unittest.mock import MagicMock

import pytest

from agent.character.character import Character
from agent.jobs.cleric import Cleric, LifeDomain
from agent.mechanics.dice_roller import DiceRoll
from agent.models.config import AgentConfig
from agent.models.decision import DecisionResult
from agent.models.enums import FeatureId
from agent.models.map import GameMap
from agent.models.position import Position
from agent.models.state import State
from tests.conftest import advance_turn


@pytest.mark.asyncio
async def test_evocation(config: AgentConfig, game_map: GameMap, actor: Character, target: Character) -> None:
    hero_id = actor.id
    actor.level = 3
    actor.change_job(Cleric.apply_specialization(LifeDomain))
    orc_id = target.id

    starting_hp = 14
    target.attributes.hp = starting_hp

    state = State(
        map=game_map,
        characters={actor.id: actor, target.id: target},
        parties={actor.party.id: actor.party, target.party.id: target.party},
        turn_order=[hero_id, orc_id],
    )

    actor._dice = MagicMock()
    value1 = 5
    actor._dice.roll_with_context.return_value = DiceRoll(expression="1d20", rolls=[], total=value1, raw=value1)
    actor._dice.roll_once.return_value = DiceRoll(expression="1d20", rolls=[], total=value1, raw=value1)

    # Turn 1.1: Hero summons sword
    evo_id = FeatureId.SPIRITUAL_SWORD.value
    evo_attack_id = FeatureId.SPIRITUAL_SWORD.value + "-" + "melee_spell_attack"
    evo_move_id = FeatureId.SPIRITUAL_SWORD.value + "-" + FeatureId.REPOSITION_EVOCATION.value

    target_pos = Position(x=target.pos.x + 1, y=target.pos.y)
    state = await advance_turn(
        state,
        result=DecisionResult(action_id=evo_id, target_position=target_pos, description=""),
    )
    assert len(state.current_actor.evocations) == 1
    assert state.current_actor.evocations[0].position == target_pos
    assert target.attributes.hp < starting_hp

    # After summon, the evo attacks should not be immediately available
    assert len(state.current_actor.evocations[0].available_actions()) == 0

    # Go back to actor's turn
    state = await advance_turn(state, result=DecisionResult(action_id="wait", description=""))
    state = await advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    assert state.current_actor.id == actor.id

    new_target_pos = Position(x=target.pos.x, y=target.pos.y + 1)
    state = await advance_turn(
        state, result=DecisionResult(action_id=evo_move_id, target_position=new_target_pos, description="")
    )
    assert len(state.current_actor.evocations) == 1
    assert state.current_actor.evocations[0].position == new_target_pos
    assert len(state.current_actor.evocations[0].available_actions()) == 1
    assert state.current_actor.evocations[0].available_actions()[0].id == evo_attack_id

    state = await advance_turn(
        state, result=DecisionResult(action_id=evo_attack_id, target_hits={target.id: 1}, description="")
    )
    assert len(state.current_actor.evocations) == 1
    # Still 1 action available at the evocation level...
    assert len(state.current_actor.evocations[0].available_actions()) == 1
    # ... but no bonus action at the character level
    assert state.current_actor.action_economy.can_use_bonus() is False
