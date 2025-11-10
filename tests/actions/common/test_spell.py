from pytest_mock import MockerFixture

from agent.actions.common.spell import AttackSpellAction
from agent.character.character import Character
from agent.character.proficiency import Proficiency, ProficiencyType
from agent.character.resolvers.roll import D20
from agent.character.resources import SpellLevel
from agent.character.stats import StatType
from agent.mechanics.dice_roller import DiceRoll
from agent.models.context import CombatContext
from agent.models.damage import DamageType
from agent.models.enums import TargetingType


def make_attack_spell_action() -> AttackSpellAction:
    return AttackSpellAction(
        id="spell",
        name="Basic Spell",
        description="A test spell.",
        targeting=TargetingType.SINGLE,
        damage_dice="1d8",
        damage_type=DamageType.FIRE,
        level=SpellLevel.LEVEL_1,
        stat=StatType.INT,
        range=1.5,
    )


def test_attack_hits(actor: Character, target: Character, mocker: MockerFixture) -> None:
    actor.attributes.intelligence = 16  # +3 modifier
    actor.attributes.spellcasting_stat = StatType.INT
    action = make_attack_spell_action()

    target._dice = mocker.MagicMock()
    save_roll = actor.spell_save_dc - 1
    target._dice.roll_with_context.return_value = DiceRoll(
        expression=D20, rolls=[save_roll], total=save_roll, raw=save_roll
    )

    actor._dice = mocker.MagicMock()
    damage_roll = 5
    actor._dice.roll_once.return_value = DiceRoll(
        expression="1d8+3", rolls=[damage_roll], total=damage_roll + 3, raw=damage_roll
    )

    start_hp = target.attributes.hp
    action.execute(actor, target, ctx=CombatContext())

    assert target.attributes.hp == start_hp - damage_roll - 3
    target._dice.roll_with_context.assert_called_once_with(dice_expression="1d20+2", advantage=True)
    actor._dice.roll_once.assert_called_once_with("1d8+3")

    action.finalize(actor)
    assert actor.action_economy.standard_actions == 0
    assert action.is_available(actor.action_economy) is False


def test_attack_misses(actor: Character, target: Character, mocker: MockerFixture) -> None:
    actor.attributes.spellcasting_stat = StatType.INT
    target.attributes.proficiencies = [Proficiency(type=ProficiencyType.SAVE, value=StatType.INT)]  # Save modifier +2
    action = make_attack_spell_action()

    actor._dice = mocker.MagicMock()
    target._dice = mocker.MagicMock()
    save_roll = actor.spell_save_dc + 1
    target._dice.roll_with_context.return_value = DiceRoll(
        expression=D20, rolls=[save_roll], total=save_roll + 2, raw=save_roll
    )

    start_hp = target.attributes.hp
    action.execute(actor, target, ctx=CombatContext())

    assert target.attributes.hp == start_hp
    target._dice.roll_with_context.assert_called_once_with(dice_expression="1d20+2", advantage=True)
    actor._dice.roll_once.assert_not_called()

    action.finalize(actor)
    assert actor.action_economy.standard_actions == 0
    assert action.is_available(actor.action_economy) is False


def test_save_throw_skipped(actor: Character, target: Character, mocker: MockerFixture) -> None:
    actor.attributes.spellcasting_stat = StatType.INT
    action = make_attack_spell_action()
    action.requires_save = False

    target._dice = mocker.MagicMock()
    actor._dice = mocker.MagicMock()
    damage_roll = 5
    actor._dice.roll_once.return_value = DiceRoll(
        expression="1d8+0", rolls=[damage_roll], total=damage_roll, raw=damage_roll
    )

    start_hp = target.attributes.hp
    action.execute(actor, target, ctx=CombatContext())

    assert target.attributes.hp == start_hp - damage_roll
    target._dice.roll_with_context.assert_not_called()
    actor._dice.roll_once.assert_called_once_with("1d8+0")

    action.finalize(actor)
    assert actor.action_economy.standard_actions == 0
    assert action.is_available(actor.action_economy) is False
