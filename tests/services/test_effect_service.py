"""Tests for EffectService."""

from agent.character.abilities import AbilityType
from agent.character.character import Character
from agent.effects.status_effects.base import StatusEffect, StatusType
from agent.effects.status_effects.collection import Blessed, Stunned
from agent.mechanics.dice_roller import DiceRoller
from agent.services.effect_service import EffectService


def test_has_condition(fighter: Character) -> None:
    """Test checking if character has a condition."""
    assert not EffectService.has_condition(fighter, StatusType.CUSTOM)

    # Add condition
    custom_effect = StatusEffect(type=StatusType.CUSTOM, save_dc=0, traits=[], duration=1)
    EffectService.apply_condition(fighter, custom_effect)

    assert EffectService.has_condition(fighter, StatusType.CUSTOM)


def test_apply_condition(fighter: Character) -> None:
    """Test applying a status effect."""
    initial_count = len(fighter.status_effects)

    custom_effect = StatusEffect(type=StatusType.CUSTOM, save_dc=0, traits=[], duration=2)
    EffectService.apply_condition(fighter, custom_effect)

    assert len(fighter.status_effects) == initial_count + 1
    assert EffectService.has_condition(fighter, StatusType.CUSTOM)


def test_apply_condition_replaces_existing(fighter: Character) -> None:
    """Test that applying same condition type replaces existing one."""
    # Apply first condition
    custom_effect1 = StatusEffect(type=StatusType.CUSTOM, save_dc=0, traits=[], duration=1)
    EffectService.apply_condition(fighter, custom_effect1)
    assert len(fighter.status_effects) == 1

    # Apply same type with different duration
    custom_effect2 = StatusEffect(type=StatusType.CUSTOM, save_dc=0, traits=[], duration=5)
    EffectService.apply_condition(fighter, custom_effect2)

    # Should still have only 1 effect, but with new duration
    assert len(fighter.status_effects) == 1
    assert fighter.status_effects[0].duration == 5


def test_remove_condition(fighter: Character) -> None:
    """Test removing a condition by type."""
    custom_effect = StatusEffect(type=StatusType.CUSTOM, save_dc=0, traits=[], duration=2)
    EffectService.apply_condition(fighter, custom_effect)
    assert EffectService.has_condition(fighter, StatusType.CUSTOM)

    EffectService.remove_condition(fighter, StatusType.CUSTOM)

    assert not EffectService.has_condition(fighter, StatusType.CUSTOM)
    assert len(fighter.status_effects) == 0


def test_try_apply_condition_with_save_success(fighter: Character) -> None:
    """Test that a successful save prevents the condition."""
    # Use deterministic dice (always roll 20)
    fighter.cheater_dice = DiceRoller(value=20)

    # Create stunned condition with save
    stunned = Stunned.with_duration(2).model_copy(update={"save_dc": 15, "save_ability": AbilityType.CON})
    result = EffectService.try_apply_condition(fighter, stunned)

    # Save should succeed (20 + CON mod >= 15)
    assert result is False
    assert not EffectService.has_condition(fighter, StatusType.STUNNED)


def test_try_apply_condition_with_save_failure(fighter: Character) -> None:
    """Test that a failed save applies the condition."""
    # Use deterministic dice (always roll 1)
    fighter.cheater_dice = DiceRoller(value=1)

    # Create stunned condition with save
    stunned = Stunned.with_duration(2).model_copy(update={"save_dc": 15, "save_ability": AbilityType.CON})
    result = EffectService.try_apply_condition(fighter, stunned)

    # Save should fail (1 + CON mod < 15)
    assert result is True
    assert EffectService.has_condition(fighter, StatusType.STUNNED)


def test_try_apply_condition_without_save(fighter: Character) -> None:
    """Test applying a condition that doesn't require a save."""
    custom_effect = StatusEffect(type=StatusType.CUSTOM, save_dc=0, traits=[], duration=1)
    result = EffectService.try_apply_condition(fighter, custom_effect)

    assert result is True
    assert EffectService.has_condition(fighter, StatusType.CUSTOM)


def test_try_expire_conditions_at_turn_start(fighter: Character) -> None:
    """Test that conditions expire at turn start."""
    # Add a condition with 1 turn duration
    custom_effect = StatusEffect(type=StatusType.CUSTOM, save_dc=0, traits=[], duration=1)
    EffectService.apply_condition(fighter, custom_effect)
    assert len(fighter.status_effects) == 1

    # Expire at turn start
    EffectService.try_expire_conditions(fighter, is_start=True)

    # Condition should be expired (duration was 1, now 0)
    assert len(fighter.status_effects) == 0


def test_try_expire_conditions_decrements_duration(fighter: Character) -> None:
    """Test that durations are decremented."""
    custom_effect = StatusEffect(type=StatusType.CUSTOM, save_dc=0, traits=[], duration=3)
    EffectService.apply_condition(fighter, custom_effect)

    # First turn
    EffectService.try_expire_conditions(fighter, is_start=True)
    assert len(fighter.status_effects) == 1
    assert fighter.status_effects[0].duration == 2

    # Second turn
    EffectService.try_expire_conditions(fighter, is_start=True)
    assert len(fighter.status_effects) == 1
    assert fighter.status_effects[0].duration == 1

    # Third turn
    EffectService.try_expire_conditions(fighter, is_start=True)
    assert len(fighter.status_effects) == 0


def test_is_immune_to(fighter: Character) -> None:
    """Test immunity check (currently always returns False)."""
    # TODO: Implement immunity system
    assert EffectService.is_immune_to(fighter, StatusType.CUSTOM) is False


def test_multiple_conditions(fighter: Character) -> None:
    """Test having multiple conditions at once."""
    custom_effect = StatusEffect(type=StatusType.CUSTOM, save_dc=0, traits=[], duration=2)
    blessed = Blessed.with_duration(3)
    EffectService.apply_condition(fighter, custom_effect)
    EffectService.apply_condition(fighter, blessed)

    assert len(fighter.status_effects) == 2
    assert EffectService.has_condition(fighter, StatusType.CUSTOM)
    assert EffectService.has_condition(fighter, StatusType.BLESSED)
