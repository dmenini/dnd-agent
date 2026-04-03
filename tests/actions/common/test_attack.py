from agent.actions.base import ActionCategory, ActionType
from agent.actions.common.attack import AttackAction, MainHandAttackAction
from agent.character.abilities import AbilityType
from agent.character.character import Character
from agent.character.proficiency import Proficiency, ProficiencyType
from agent.effects.base import Trait
from agent.equipment.weapons import WeaponType
from agent.models.context import CombatContext
from agent.models.damage import DamageType
from agent.models.enums import EventType, FeatureId, TargetingType
from agent.services.visibility_service import VisibilityService
from tests.conftest import cheater_dice


def make_attack_action() -> AttackAction:
    """Helper for creating a deterministic melee attack."""
    return MainHandAttackAction(
        id="basic_attack",
        name="Basic Attack",
        description="A test melee strike.",
        targeting=TargetingType.SINGLE,
        damage_dice="1d8",
        damage_type=DamageType.SLASHING,
        weapon_type=WeaponType.SIMPLE_MELEE,
        ability=AbilityType.STR,
        range=1.5,
        type=ActionType.ATTACK,
        category=ActionCategory.STANDARD,
    )


def test_attack_hits(actor: Character, target: Character) -> None:
    actor.attributes.strength = 16  # +3 modifier
    actor.attributes.proficiencies = [Proficiency(type=ProficiencyType.WEAPON, target=WeaponType.SIMPLE_MELEE)]
    action = make_attack_action()

    # Set deterministic dice on actor - all rolls return 7
    actor.cheater_dice = cheater_dice(value=7)
    # Attack roll: 1d20 rolls 7, +5 modifier (STR+3, prof+2) = 12 (hits AC 0)
    # Damage roll: 1d8 rolls 7, +3 STR modifier = 10

    start_hp = target.attributes.hp
    action.execute(actor, target, ctx=CombatContext())

    assert target.attributes.hp == start_hp - 10

    action.finalize(actor)
    assert actor.action_economy.standard_actions == 0
    assert action.is_available(actor.action_economy) is False


def test_attack_misses(actor: Character, target: Character) -> None:
    action = make_attack_action()
    target.attributes.base_ac = 20  # Set high AC so attack misses

    # Set dice to roll 1
    actor.cheater_dice = cheater_dice(value=1)

    start_hp = target.attributes.hp
    action.execute(actor, target, ctx=CombatContext())

    # Target HP unchanged since attack missed (1+2=3 vs AC 20)
    assert target.attributes.hp == start_hp

    action.finalize(actor)
    assert actor.action_economy.standard_actions == 0
    assert action.is_available(actor.action_economy) is False


def test_attack_critical_hit(actor: Character, target: Character) -> None:
    action = make_attack_action()
    actor.attributes.strength = 10  # +0 modifier
    target.attributes.hp = 50  # Set high enough to survive crit

    # Natural 20 triggers critical
    actor.cheater_dice = cheater_dice(value=20)

    start_hp = target.attributes.hp
    action.execute(actor, target, ctx=CombatContext())

    # Attack roll: raw=20 triggers crit
    # Damage: cheater_dice returns 20, doubled for crit = 40
    assert target.attributes.hp == start_hp - 40

    action.finalize(actor)
    assert actor.action_economy.standard_actions == 0
    assert action.is_available(actor.action_economy) is False


def test_attack_breaks_stealth(actor: Character, target: Character) -> None:
    VisibilityService.hide(actor)
    actor.passives.append(Trait(feature_id=FeatureId.STEALTH, source_id="hide", event_type=EventType.MODIFIER))
    action = make_attack_action()
    action.execute(actor, target, ctx=CombatContext())
    action.finalize(actor)

    assert actor.action_economy.standard_actions == 0
    assert action.is_available(actor.action_economy) is False
    assert actor.is_hidden is False
    assert actor.stealth_value == 0
