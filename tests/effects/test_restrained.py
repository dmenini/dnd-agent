from unittest.mock import MagicMock

from agent.character.attributes import Attributes
from agent.character.character import Character, Party
from agent.character.stats import StatType
from agent.effects.base import EffectType
from agent.effects.restrained import Restrained
from agent.equipment.weapons import MeleeWeapon, WeaponType
from agent.mechanics.dice_roller import DiceRoll
from agent.models.config import AgentConfig
from agent.models.damage import DamageType
from agent.models.enums import TargetingType
from agent.models.position import Position
from agent.models.state import DecisionResult, State
from tests.conftest import advance_turn


def test_restrained(
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
        effects=[Restrained(duration=2)],
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

    starting_hp = 20
    orc = Character(
        id=orc_id,
        name="Orc Grunt",
        icon="👹",
        attributes=Attributes(hp=starting_hp),
        pos=Position(x=4, y=2),
        party=party_enemies,
        main_hand=MeleeWeapon(
            name="Sword",
            damage_dice="2d6",
            range=2,
            targeting=TargetingType.SINGLE,
            weapon_type=WeaponType.SIMPLE_MELEE,
            damage_type=DamageType.SLASHING,
        ),
    )

    state = State(
        characters={hero.id: hero, orc.id: orc},
        parties={party_players.id: party_players, party_enemies.id: party_enemies},
        turn_order=[hero_id, orc_id],
    )

    hero._dice = MagicMock()  # fail attack roll, but with autocrit attacks anyway
    value = 5
    hero._dice.roll_with_context.return_value = DiceRoll(expression="1d20", rolls=[], total=value, raw=value)
    hero._dice.roll_once.return_value = DiceRoll(expression="1d20", rolls=[], total=value, raw=value)
    hero._dice.roll_twice.return_value = DiceRoll(expression="2d20", rolls=[], total=value * 2, raw=value)

    # Turn 1.1: Hero attacks and applies restrained
    state = advance_turn(
        state, result=DecisionResult(action_id="main_hand_attack", target_ids=[orc_id], description="")
    )
    orc = state.characters[orc_id]
    assert orc.attributes.hp == starting_hp - value
    assert orc.status_effects[0].type == EffectType.RESTRAINED
    assert orc.status_effects[0].duration == 2
    assert orc.attributes._modifiers["advantage.defense"][0].value == 1
    assert orc.attributes._modifiers["advantage.attack"][0].value == -1
    assert orc.attributes._modifiers["save_advantage.dex"][0].value == -1
    assert orc.attributes.compute_advantage("defense") == 1
    assert orc.attributes.compute_advantage("attack") == -1
    assert orc.attributes.compute_save_advantage(StatType.DEX) == -1

    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 1.2: Orc restrained -> after attack no more actions available and passes (no need to wait)
    state = advance_turn(
        state, result=DecisionResult(action_id="main_hand_attack", target_ids=[hero_id], description="")
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
    assert orc.attributes._modifiers["defense_advantage"] == []
    assert orc.attributes._modifiers["attack_advantage"] == []
    assert orc.attributes._modifiers["dex_save_advantage"] == []
