"""Tests for VisibilityService."""

from agent.character.character import Character
from agent.models.enums import FeatureId
from agent.services.visibility_service import VisibilityService
from tests.conftest import cheater_dice


def test_hide(fighter: Character) -> None:
    """Test hide sets stealth value and registers passive."""
    fighter.cheater_dice = cheater_dice(value=15)

    assert fighter.stealth_value == 0
    assert not any(p.source_id == "hide" for p in fighter.passives)

    VisibilityService.hide(fighter)

    # Should set stealth value to roll result (15 + DEX mod)
    assert fighter.stealth_value > 0
    # Should register attacker advantage passive (from hiding)
    assert any(p.feature_id == FeatureId.ATTACKER_ADVANTAGE and p.source_id == "hide" for p in fighter.passives)


def test_unhide(fighter: Character) -> None:
    """Test unhide clears stealth value and unregisters passive."""
    fighter.cheater_dice = cheater_dice(value=15)
    VisibilityService.hide(fighter)

    assert fighter.stealth_value > 0
    assert fighter.is_hidden

    VisibilityService.unhide(fighter)

    assert fighter.stealth_value == 0
    assert not fighter.is_hidden
    assert not any(p.source_id == "hide" for p in fighter.passives)


def test_detect_target_visible_target(fighter: Character, orc: Character) -> None:
    """Test detect_target returns True for visible (non-hidden) targets."""
    assert not orc.is_hidden

    result = VisibilityService.detect_target(fighter, orc, use_passive=True)

    assert result is True


def test_detect_target_hidden_target_with_high_stealth(fighter: Character, orc: Character) -> None:
    """Test detect_target returns False when target's stealth beats perception."""
    orc.cheater_dice = cheater_dice(value=20)
    VisibilityService.hide(orc)

    # Orc has high stealth (20 + DEX mod), fighter has passive perception around 12
    result = VisibilityService.detect_target(fighter, orc, use_passive=True)

    assert result is False


def test_detect_target_hidden_target_with_low_stealth(fighter: Character, orc: Character) -> None:
    """Test detect_target returns True when perception beats target's stealth."""
    orc.cheater_dice = cheater_dice(value=1)
    VisibilityService.hide(orc)

    # Orc has low stealth (1 + DEX mod), fighter has passive perception around 12
    result = VisibilityService.detect_target(fighter, orc, use_passive=True)

    assert result is True


def test_detect_target_with_active_perception(fighter: Character, orc: Character) -> None:
    """Test detect_target uses active perception roll when use_passive=False."""
    orc.cheater_dice = cheater_dice(value=15)
    VisibilityService.hide(orc)

    fighter.cheater_dice = cheater_dice(value=18)

    # Active perception roll (18 + WIS mod) should beat stealth (15 + DEX mod)
    result = VisibilityService.detect_target(fighter, orc, use_passive=False)

    assert result is True
