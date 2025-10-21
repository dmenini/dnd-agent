
from pytest_mock import MockerFixture

from agent.actions.base import ActionCategory, ActionType
from agent.actions.common.attack import AttackAction
from agent.character.character import Character
from agent.character.resolvers.roll import D20
from agent.character.stats import StatType
from agent.equipment.weapons import WeaponType
from agent.mechanics.dice_roller import DiceRoll
from agent.models.damage import DamageType
from agent.models.enums import TargetingType


def make_attack_action() -> AttackAction:
    """Helper for creating a deterministic melee attack."""
    return AttackAction(
        id="basic_attack",
        name="Basic Attack",
        description="A test melee strike.",
        targeting=TargetingType.SINGLE,
        damage_dice="1d8",
        damage_type=DamageType.SLASHING,
        weapon_type=WeaponType.SIMPLE_MELEE,
        stat=StatType.STR,
        range=1.5,
        action_type=ActionType.ATTACK,
        category=ActionCategory.STANDARD,
    )


def test_attack_hits(actor: Character, target: Character, mocker: MockerFixture) -> None:
    """Attacker rolls high enough to hit target and deals damage."""
    actor.attributes.strength = 16  # +3 modifier
    actor.proficiencies = [WeaponType.SIMPLE_MELEE]
    roll1 = target.armor_class + 1
    roll2 = 10
    action = make_attack_action()

    actor._dice = mocker.MagicMock()
    actor._dice.roll_with_context.return_value = DiceRoll(expression=D20, rolls=[roll1], total=roll1, raw=roll1)
    actor._dice.roll_once.return_value = DiceRoll(expression="1d8+5", rolls=[5], total=roll2, raw=5)

    start_hp = target.attributes.hp
    action.execute(actor, target)

    assert target.attributes.hp == start_hp - roll2
    actor._dice.roll_with_context.assert_called_once_with(dice_expression=D20, advantage=True)
    actor._dice.roll_once.assert_called_once_with("1d8+5")


def test_attack_misses(actor: Character, target: Character, mocker: MockerFixture) -> None:
    """Attack roll is too low, no damage applied."""
    roll = target.armor_class - 1
    action = make_attack_action()

    actor._dice = mocker.MagicMock()
    actor._dice.roll_with_context.return_value = DiceRoll(expression=D20, rolls=[roll], total=roll, raw=roll)

    start_hp = target.attributes.hp
    action.execute(actor, target)

    # Target HP unchanged since attack missed
    assert target.attributes.hp == start_hp
    actor._dice.roll_once.assert_not_called()


def test_attack_critical_hit(actor: Character, target: Character, mocker: MockerFixture) -> None:
    """Critical hit (natural 20) deals double dice damage."""
    action = make_attack_action()
    roll2 = 5

    actor._dice = mocker.MagicMock()
    actor._dice.roll_with_context.return_value = DiceRoll(expression=D20, rolls=[20], total=20, raw=20)
    actor._dice.roll_twice.return_value = DiceRoll(expression="1d8+0", rolls=[roll2], total=roll2, raw=roll2)

    start_hp = target.attributes.hp
    action.execute(actor, target)

    # Target takes full critical damage
    assert target.attributes.hp == start_hp - roll2
    actor._dice.roll_with_context.assert_called_once_with(dice_expression=D20, advantage=None)
    actor._dice.roll_twice.assert_called_once_with("1d8+0")
