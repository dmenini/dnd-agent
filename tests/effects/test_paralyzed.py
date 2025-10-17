from unittest.mock import MagicMock

from agent.character.attributes import Attributes
from agent.character.character import Character, Party
from agent.character.stats import StatType
from agent.effects.base import EffectType
from agent.effects.paralyzed import Paralyzed
from agent.equipment.weapons import MeleeWeapon, WeaponType
from agent.mechanics.dice_roller import DiceRoll
from agent.models.config import AgentConfig
from agent.models.damage import DamageType
from agent.models.enums import TargetingType
from agent.models.position import Position
from agent.models.state import DecisionResult, State
from tests.conftest import advance_turn


def test_paralyzed(
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
        effects=[Paralyzed(duration=2)],
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

    # Turn 1.1: Hero attacks and applies paralysis
    state = advance_turn(
        state, result=DecisionResult(action_id="main_hand_attack", target_ids=[orc_id], description="")
    )
    orc = state.characters[orc_id]
    assert orc.attributes.hp == starting_hp - value
    assert orc.status_effects[0].type == EffectType.PARALYZED
    assert orc.status_effects[0].duration == 2
    assert orc.attributes._modifiers["advantage.defense"][0].value is True
    assert orc.attributes._modifiers["save_autofail.str"][0].value is True
    assert orc.attributes._modifiers["save_autofail.dex"][0].value is True

    assert orc.attributes.compute_advantage("defense") == 1
    assert orc.attributes.compute_save_autofail(StatType.STR) is True
    assert orc.attributes.compute_save_autofail(StatType.DEX) is True

    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 1.2: Orc paralyzed -> skip turn
    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))
    assert state.action is None
    assert state.decision is None

    orc = state.characters[orc_id]
    assert orc.status_effects[0].type == EffectType.PARALYZED
    assert orc.status_effects[0].duration == 1

    # Turn 2.1: Hero attacks -> crit
    state = advance_turn(
        state, result=DecisionResult(action_id="main_hand_attack", target_ids=[orc_id], description="")
    )
    crit_damage = value + value
    assert orc.attributes.hp == starting_hp - value - crit_damage

    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 2.2: Orc still paralyzed -> skip turn
    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))
    assert state.action is None
    assert state.decision is None

    # Paralysis expires after 2 turns
    orc = state.current_actor
    assert len(orc.status_effects) == 0
    assert orc.attributes._modifiers["defense_advantage"] == []
    assert orc.attributes._modifiers["str_save_autofail"] == []
    assert orc.attributes._modifiers["dex_save_autofail"] == []
