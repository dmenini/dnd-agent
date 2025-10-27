from pytest_mock import MockerFixture

from agent.actions.base import ActionCategory, ActionType
from agent.actions.common.attack import AttackAction, MainHandAttackAction
from agent.character.character import Character
from agent.character.resolvers.roll import D20
from agent.character.stats import StatType
from agent.effects.base import Trait
from agent.equipment.weapons import WeaponType
from agent.mechanics.dice_roller import DiceRoll
from agent.models.context import CombatContext
from agent.models.damage import DamageType
from agent.models.enums import FeatureId, TargetingType


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
        stat=StatType.STR,
        range=1.5,
        type=ActionType.ATTACK,
        category=ActionCategory.STANDARD,
    )


def test_attack_hits(actor: Character, target: Character, mocker: MockerFixture) -> None:
    actor.attributes.strength = 16  # +3 modifier
    actor.attributes.weapon_proficiencies = [WeaponType.SIMPLE_MELEE]
    roll1 = target.armor_class + 1  # Attacker rolls high enough to hit target
    roll2 = 10
    action = make_attack_action()

    actor._dice = mocker.MagicMock()
    actor._dice.roll_with_context.return_value = DiceRoll(expression=D20, rolls=[roll1], total=roll1, raw=roll1)
    actor._dice.roll_once.return_value = DiceRoll(expression="1d8+5", rolls=[5], total=roll2, raw=5)

    start_hp = target.attributes.hp
    action.execute(actor, target, ctx=CombatContext())

    assert target.attributes.hp == start_hp - roll2
    actor._dice.roll_with_context.assert_called_once_with(dice_expression=D20, advantage=True)
    actor._dice.roll_once.assert_called_once_with("1d8+5")

    action.finalize(actor)
    assert actor.action_economy.standard_actions == 0
    assert action.is_available(actor.action_economy) is False


def test_attack_misses(actor: Character, target: Character, mocker: MockerFixture) -> None:
    roll = target.armor_class - 1  # Attack roll is too low -> miss
    action = make_attack_action()

    actor._dice = mocker.MagicMock()
    actor._dice.roll_with_context.return_value = DiceRoll(expression=D20, rolls=[roll], total=roll, raw=roll)

    start_hp = target.attributes.hp
    action.execute(actor, target, ctx=CombatContext())

    # Target HP unchanged since attack missed
    assert target.attributes.hp == start_hp
    actor._dice.roll_once.assert_not_called()

    action.finalize(actor)
    assert actor.action_economy.standard_actions == 0
    assert action.is_available(actor.action_economy) is False


def test_attack_critical_hit(actor: Character, target: Character, mocker: MockerFixture) -> None:
    action = make_attack_action()
    roll2 = 5

    actor._dice = mocker.MagicMock()
    actor._dice.roll_with_context.return_value = DiceRoll(expression=D20, rolls=[20], total=20, raw=20)
    actor._dice.roll_twice.return_value = DiceRoll(expression="1d8+0", rolls=[roll2], total=roll2, raw=roll2)

    start_hp = target.attributes.hp
    action.execute(actor, target, ctx=CombatContext())

    # Target takes full critical damage
    assert target.attributes.hp == start_hp - roll2
    actor._dice.roll_with_context.assert_called_once_with(dice_expression=D20, advantage=None)
    actor._dice.roll_twice.assert_called_once_with("1d8+0")  # double dice damage

    action.finalize(actor)
    assert actor.action_economy.standard_actions == 0
    assert action.is_available(actor.action_economy) is False


def test_attack_breaks_stealth(actor: Character, target: Character) -> None:
    actor.hide()
    actor.passives.append(Trait(feature_id=FeatureId.STEALTH, source_id="hide"))
    action = make_attack_action()
    action.execute(actor, target, ctx=CombatContext())
    action.finalize(actor)

    assert actor.action_economy.standard_actions == 0
    assert action.is_available(actor.action_economy) is False
    assert actor.is_hidden is False
    assert actor.stealth_value == 0
