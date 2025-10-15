from unittest.mock import MagicMock

from agent.character.character import Character, Party
from agent.effects.base import EffectType
from agent.effects.hasted import Hasted
from agent.mechanics.dice_roller import DiceRoll
from agent.models.config import AgentConfig
from agent.models.enums import DamageType, TargetingType, WeaponType
from agent.models.position import Position
from agent.models.state import DecisionResult, State
from agent.models.weapons import MeleeWeapon, SupportSpell
from tests.conftest import advance_turn


def test_hasted(config: AgentConfig, ) -> None:
    hero_id = "hero"
    orc_id = "orc"

    party_players = Party(id="p1", name="Heroes", is_player_party=True)
    party_enemies = Party(id="p2", name="Enemies", is_player_party=False)

    sword = MeleeWeapon(
        name="Sword",
        damage_dice="1d5",
        weapon_type=WeaponType.LONGSWORD,
        range=5,
        targeting=TargetingType.SINGLE,
    )

    haste = SupportSpell(
        name="Haste",
        description="Gain 1 extra action on the next 2 turns",
        range=1,
        targeting=TargetingType.SELF,
        status_effects=[Hasted(duration=1)],
    )
    hero = Character(
        id=hero_id,
        name="Alfred",
        icon="⚔️",
        pos=Position(x=2, y=2),
        is_player=True,
        party=party_players,
        spells=[haste],
        main_hand=sword,
    )
    orc = Character(
        id=orc_id,
        name="Orc Grunt",
        icon="👹",
        pos=Position(x=4, y=2),
        party=party_enemies,
    )

    state = State(
        characters={hero.id: hero, orc.id: orc},
        parties={party_players.id: party_players, party_enemies.id: party_enemies},
        turn_order=[hero_id, orc_id],
    )

    # Turn 1.1: Hero casts Haste on self
    state = advance_turn(state, result=DecisionResult(action_id="cast_haste", target_ids=[hero_id], description=""))
    hero = state.characters[hero_id]
    effects = [eff for eff in hero.status_effects]
    assert effects[0].type == EffectType.HASTED
    assert effects[0].duration == 2
    assert hero.attributes._modifiers["ac"][0].value == 2
    assert hero.attributes._modifiers["speed"][0].value == 2
    assert hero.attributes._modifiers["dex_save_advantage"][0].value == 1

    assert hero.ac == 4
    assert hero.current_speed == 12.0
    assert hero.attributes.compute_advantage("dex_save") == 1

    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 1.2: Orc pass
    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 2.1: Hero double action -> haste expires, lethargy takes place at the end of turn
    effects = [eff for eff in state.current_actor.status_effects]
    assert effects[0].type == EffectType.HASTED
    assert effects[0].duration == 1
    state = advance_turn(state, result=DecisionResult(action_id="main_hand_attack", target_ids=[orc_id], description=""))
    state = advance_turn(state, result=DecisionResult(action_id="main_hand_attack", target_ids=[orc_id], description=""))

    hero._dice = MagicMock()  # fail save
    hero._dice.roll_with_context.return_value = DiceRoll(expression="1d20", rolls=[], total=1, raw=1)
    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    hero = state.characters[hero_id]
    effects = [eff for eff in hero.status_effects]
    assert effects[0].type == EffectType.LETHARGIC
    assert effects[0].duration == 1
    assert hero.attributes._modifiers["speed"][0].value == 0.5
    assert hero.attributes._modifiers["wis_save_advantage"][0].value == -1

    # Turn 2.2: Pass
    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 3.1: Still performs one action despite lethargy, which then expires
    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))
    assert state.action is not None
    assert len(state.current_actor.status_effects) == 0

