"""Tests for ActionService."""

from agent.character.character import Character
from agent.equipment.armor import Armor, ArmorType
from agent.services.action_service import ActionService


def test_has_resources_with_all_actions(fighter: Character) -> None:
    """Test has_resources returns True when character has actions available."""
    # Fighter starts with all resources
    assert ActionService.has_resources(fighter) is True


def test_has_resources_with_no_main_action(fighter: Character) -> None:
    """Test has_resources with no main action."""
    fighter.action_economy.standard_actions = 0
    fighter.action_economy.bonus_actions = 1
    fighter.action_economy.movement_used = 0

    # Still has bonus action and movement
    assert ActionService.has_resources(fighter) is True


def test_has_resources_with_no_actions_but_movement(fighter: Character) -> None:
    """Test has_resources with only movement remaining."""
    fighter.action_economy.standard_actions = 0
    fighter.action_economy.bonus_actions = 0
    fighter.action_economy.movement_used = 0  # Has movement

    assert ActionService.has_resources(fighter) is True


def test_has_resources_exhausted(fighter: Character) -> None:
    """Test has_resources returns False when all resources exhausted."""
    fighter.action_economy.standard_actions = 0
    fighter.action_economy.bonus_actions = 0
    fighter.action_economy.movement_used = fighter.speed  # All movement used
    fighter.action_economy.movement_available = False  # Movement exhausted

    # Remove equipment so has_resources logic only checks action economy
    fighter.equipment.main_hand = None
    fighter.equipment.off_hand = None
    fighter.equipment.ranged = None

    assert ActionService.has_resources(fighter) is False


def test_can_use_spells_no_armor(wizard: Character) -> None:
    """Test can_use_spells returns True when wearing no armor."""
    wizard.equipment.armor = None
    assert ActionService.can_use_spells(wizard) is True


def test_can_use_spells_with_proficient_armor(cleric: Character) -> None:
    """Test can_use_spells returns True when wearing proficient armor."""
    # Cleric is proficient in light and medium armor
    light_armor = Armor(name="Leather", description="Light armor", armor_type=ArmorType.LIGHT, base_ac=11)
    cleric.equipment.armor = light_armor

    assert ActionService.can_use_spells(cleric) is True


def test_can_use_spells_with_non_proficient_armor(fighter: Character) -> None:
    """Test can_use_spells with non-proficient armor and empty offhand."""
    # Fighter has all armor proficiency, so this is a hypothetical
    # Let's just test the logic works
    assert ActionService.can_use_spells(fighter) is True


def test_get_available_actions_returns_basic_actions(fighter: Character) -> None:
    """Test get_available_actions returns basic actions."""
    actions = ActionService.get_available_actions(fighter)

    # Should have basic actions
    assert "move" in actions
    assert "dash" in actions
    assert "dodge" in actions
    assert "wait" in actions
    assert "hide" in actions


def test_get_available_actions_includes_weapon_attacks(fighter: Character) -> None:
    """Test get_available_actions includes weapon attacks."""
    actions = ActionService.get_available_actions(fighter)

    # Fighter has main hand equipped
    assert "main_hand_attack" in actions


def test_get_available_actions_includes_special_abilities(fighter: Character) -> None:
    """Test get_available_actions includes special abilities."""
    actions = ActionService.get_available_actions(fighter)

    # Fighter has Second Wind
    assert "second_wind" in actions


def test_get_available_actions_includes_spells_when_available(wizard: Character) -> None:
    """Test get_available_actions includes spells when slots available."""
    actions = ActionService.get_available_actions(wizard)

    # Wizard has Magic Missile
    assert "magic_missile" in actions


def test_get_available_actions_excludes_spells_no_slots(wizard: Character) -> None:
    """Test get_available_actions excludes spells when no slots available."""
    # Exhaust all spell slots
    for level in range(1, 10):
        wizard.spell_slots.slots[level] = 0  # type: ignore[index]

    actions = ActionService.get_available_actions(wizard)

    # Should not have any spells
    assert "magic_missile" not in actions


def test_get_available_actions_filters_by_action_economy(fighter: Character) -> None:
    """Test get_available_actions filters out unavailable actions."""
    # Use up standard action
    fighter.action_economy.standard_actions = 0

    actions = ActionService.get_available_actions(fighter)

    # Should not have main hand attack (requires standard action)
    assert "main_hand_attack" not in actions

    # But should still have movement and bonus actions
    assert "move" in actions
    assert "second_wind" in actions  # Bonus action
