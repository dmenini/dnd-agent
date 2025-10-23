from unittest.mock import MagicMock

from agent.actions.common.spell import SupportSpellAction
from agent.character.character import Character
from agent.character.resources import SpellLevel
from agent.character.stats import StatType
from agent.effects.base import EffectType
from agent.effects.status_effects.hasted import Hasted
from agent.jobs.feature import FeatureId
from agent.mechanics.dice_roller import DiceRoll
from agent.models.config import AgentConfig
from agent.models.decision import DecisionResult
from agent.models.enums import TargetingType
from agent.models.map import GameMap
from agent.models.state import State
from tests.conftest import advance_turn


def test_hasted(config: AgentConfig, game_map: GameMap, actor: Character, target: Character) -> None:
    hero_id = actor.id
    orc_id = target.id

    haste = SupportSpellAction(
        id=FeatureId.HASTE.value,
        name="Haste",
        description="Gain 1 extra action on the next 2 turns",
        range=1,
        targeting=TargetingType.SELF,
        status_effects=[Hasted(duration=1)],
        level=SpellLevel.LEVEL_1,
        stat=StatType.WIS,
    )
    actor.spells = [haste]

    state = State(
        map=game_map,
        characters={actor.id: actor, target.id: target},
        parties={actor.party.id: actor.party, target.party.id: target.party},
        turn_order=[hero_id, orc_id],
    )

    # Turn 1.1: Hero casts Haste on self
    state = advance_turn(
        state, result=DecisionResult(action_id=FeatureId.HASTE.value, target_hits={hero_id: 1}, description="")
    )
    hero = state.characters[hero_id]
    assert hero.status_effects[0].type == EffectType.HASTED
    assert hero.status_effects[0].duration == 1
    assert hero.attributes.get_modifiers("ac")[0].value == 2
    assert hero.attributes.get_modifiers("speed")[0].value == 2
    assert hero.attributes.get_modifiers("save_advantage.dex")[0].value is True

    assert hero.armor_class == 12
    assert hero.current_speed == 12.0
    assert hero.attributes.stat_save_advantage(StatType.DEX) == 1

    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 1.2: Orc pass
    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 2.1: Hero double action -> haste expires, lethargy takes place at the end of turn
    assert state.current_actor.status_effects[0].type == EffectType.HASTED
    assert state.current_actor.status_effects[0].duration == 1
    state = advance_turn(
        state, result=DecisionResult(action_id="main_hand_attack", target_hits={orc_id: 1}, description="")
    )
    state = advance_turn(
        state, result=DecisionResult(action_id="main_hand_attack", target_hits={orc_id: 1}, description="")
    )

    hero._dice = MagicMock()  # fail save
    hero._dice.roll_with_context.return_value = DiceRoll(expression="1d20", rolls=[], total=1, raw=1)
    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    hero = state.characters[hero_id]
    assert hero.status_effects[0].type == EffectType.LETHARGIC
    assert hero.status_effects[0].duration == 1
    assert hero.attributes.get_modifiers("speed")[0].value == 0.5
    assert hero.attributes.get_modifiers("save_disadvantage.wis")[0].value is True

    assert hero.current_speed == 3
    assert hero.attributes.stat_save_advantage(StatType.WIS) == -1

    # Turn 2.2: Pass
    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 3.1: Still performs one action despite lethargy, which then expires
    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))
    assert state.action is not None
    assert len(state.current_actor.status_effects) == 0
