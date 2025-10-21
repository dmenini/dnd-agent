from agent.character.character import Character, Party
from agent.effects.base import EffectType
from agent.equipment.weapons import MeleeWeapon, WeaponType
from agent.models.config import AgentConfig
from agent.models.damage import DamageType
from agent.models.decision import DecisionResult
from agent.models.enums import TargetingType
from agent.models.position import Position
from agent.models.state import State
from tests.conftest import advance_turn


def test_dodge(
    config: AgentConfig,
) -> None:
    hero_id = "hero"
    orc_id = "orc"

    party_players = Party(id="p1", name="Heroes", is_player_party=True)
    party_enemies = Party(id="p2", name="Enemies", is_player_party=False)

    sword = MeleeWeapon(
        name="Sword",
        damage_dice="1d5",
        weapon_type=WeaponType.MARTIAL_MELEE,
        range=5,
        targeting=TargetingType.SINGLE,
        damage_type=DamageType.SLASHING,
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
    state = advance_turn(state, result=DecisionResult(action_id="dodge", target_hits={hero_id: 1}, description=""))
    hero = state.characters[hero_id]
    assert hero.status_effects[0].type == EffectType.DODGING
    assert hero.status_effects[0].duration == 1
    assert hero.attributes.get_modifiers("disadvantage.defense")[0].value is True

    assert hero.attributes.advantage("defense") == -1

    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 1.2: Orc pass
    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))

    # Turn 2.1: Dodge expires
    assert state.current_actor.status_effects[0].type == EffectType.DODGING
    assert state.current_actor.status_effects[0].duration == 1
    state = advance_turn(state, result=DecisionResult(action_id="wait", description=""))
    assert len(state.current_actor.status_effects) == 0
