from pytest_mock import MockerFixture

from agent.actions.base import ActionType
from agent.actions.common.attack import MainHandAttackAction, OffHandAttackAction
from agent.character.abilities import AbilityType
from agent.character.character import Character
from agent.effects.trait_effects.damage import (
    auto_crit_if_melee_effect,
    damage_bonus_effect,
    damage_multiplier_effect,
    damage_over_time_effect,
    ignore_resistance_effect,
    reflect_melee_damage_effect,
    sneak_attack_effect,
)
from agent.equipment.weapons import WeaponType
from agent.mechanics.dice_roller import DiceRoll
from agent.models.context import CombatContext
from agent.models.damage import Damage, DamageComponent, DamageResistance, DamageType, DamageVulnerability
from agent.models.enums import TargetingType
from agent.models.position import Position

MELEE_RANGE = 5


def test_auto_crit_triggers_within_melee(actor: Character, target: Character, context: CombatContext) -> None:
    auto_crit_if_melee_effect(actor, target, context)
    assert context.is_critical is True


def test_auto_crit_does_not_trigger_outside_melee(actor: Character, target: Character, context: CombatContext) -> None:
    target.pos = Position(x=10, y=10)
    auto_crit_if_melee_effect(actor, target, context)
    assert context.is_critical is False


def test_damage_over_time_applies(target: Character) -> None:
    start_hp = target.attributes.hp
    damage_type = DamageType.FIRE
    value = 5
    damage_over_time_effect(target, value=value, damage_type=damage_type)
    assert target.attributes.hp == start_hp - value


def test_reflect_melee_applies_when_in_range(actor: Character, target: Character) -> None:
    context = CombatContext(damage=Damage(components=[DamageComponent(value=10, type=DamageType.FIRE)]))
    start_hp = target.attributes.hp
    reflect_melee_damage_effect(
        actor=actor,
        target=target,
        context=context,
        ratio=0.5,
        damage_type=DamageType.FIRE,
    )
    assert actor.attributes.hp == start_hp - 5


def test_reflect_melee_no_effect_if_no_damage(actor: Character, target: Character, context: CombatContext) -> None:
    start_hp = target.attributes.hp
    reflect_melee_damage_effect(actor, target, context, ratio=0.5, damage_type=DamageType.FIRE)
    assert actor.attributes.hp == start_hp


def test_reflect_melee_no_effect_if_no_damage_of_same_type(
    actor: Character, target: Character, context: CombatContext
) -> None:
    context = CombatContext(damage=Damage(components=[DamageComponent(value=10, type=DamageType.COLD)]))
    start_hp = target.attributes.hp
    reflect_melee_damage_effect(actor, target, context, ratio=0.5, damage_type=DamageType.FIRE)
    assert actor.attributes.hp == start_hp


def test_damage_bonus_adds_component(target: Character) -> None:
    context = CombatContext(damage=Damage(components=[]))
    value = 3
    damage_bonus_effect(target, context, value=value, damage_type=DamageType.FIRE)

    assert any(c.value == value and c.type == DamageType.FIRE for c in context.damage.components)  # type: ignore[union-attr]


def test_damage_bonus_no_effect_without_damage(target: Character, context: CombatContext) -> None:
    context.damage = None
    damage_bonus_effect(target, context, value=3, damage_type=DamageType.FIRE)
    assert context.damage is None


def test_damage_multiplier_adds_component_and_logs(target: Character) -> None:
    context = CombatContext(damage=Damage(components=[]))
    value = 2.0
    damage_multiplier_effect(target, context, value=value, damage_type=DamageType.FIRE)
    assert any(c.value == value and c.operation == "mul" for c in context.damage.components)  # type: ignore[union-attr]


def test_ignore_resistance_adds_vulnerability(actor: Character, target: Character, mocker: MockerFixture) -> None:
    target.attributes.damage_resistance = mocker.MagicMock(
        return_value=DamageResistance(value=0.5, type=DamageType.FIRE)
    )
    context = CombatContext(damage=Damage(components=[]))

    ignore_resistance_effect(actor, target, context, DamageType.FIRE)
    assert context.damage.vulnerabilities == [DamageVulnerability(value=0.5, type=DamageType.FIRE)]  # type: ignore[union-attr]


def test_ignore_resistance_no_effect_if_no_damage(actor: Character, target: Character, context: CombatContext) -> None:
    context.damage = None
    ignore_resistance_effect(actor, target, context, DamageType.FIRE)


def test_ignore_resistance_no_effect_if_no_resistance(
    actor: Character, target: Character, mocker: MockerFixture
) -> None:
    target.attributes.damage_resistance = mocker.MagicMock(return_value=None)
    context = CombatContext(damage=Damage(components=[]))
    ignore_resistance_effect(actor, target, context, DamageType.FIRE)


def test_sneak_attack_once_per_turn(actor: Character, target: Character) -> None:
    context = CombatContext(
        attack_roll=DiceRoll(expression="1d20", rolls=[10, 5], total=10, raw=10, advantage=True),
        damage=Damage(components=[DamageComponent(value=10, type=DamageType.PIERCING)]),
        metadata=MainHandAttackAction(
            targeting=TargetingType.SINGLE,
            range=3,
            damage_type=DamageType.PIERCING,
            damage_dice="1d10",
            weapon_type=WeaponType.SIMPLE_RANGE,
            ability=AbilityType.DEX,
        ).model_dump(),
    )
    sneak_attack_effect(actor, context, dice="1d6")

    assert len(context.damage.components) == 2  # type: ignore[union-attr]

    # Second attack in the same turn
    actor.action_economy.last_standard_action = ActionType.ATTACK
    context = CombatContext(
        attack_roll=DiceRoll(expression="1d20", rolls=[10, 5], total=10, raw=10, advantage=True),
        damage=Damage(components=[DamageComponent(value=10, type=DamageType.PIERCING)]),
        metadata=OffHandAttackAction(
            targeting=TargetingType.SINGLE,
            range=3,
            damage_type=DamageType.PIERCING,
            damage_dice="1d5",
            weapon_type=WeaponType.SIMPLE_MELEE,
            ability=AbilityType.DEX,
        ).model_dump(),
    )
    sneak_attack_effect(actor, context, dice="1d6")

    assert len(context.damage.components) == 1  # type: ignore[union-attr]
