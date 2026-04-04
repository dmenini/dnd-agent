"""Tests for CombatService."""

from agent.character.character import Character
from agent.services.combat_service import CombatService


def test_start_turn(fighter: Character) -> None:
    """Test start_turn restores action economy and expires start-of-turn effects."""
    # Simulate end of previous turn
    fighter.turn_done = True
    fighter.action_economy.movement_used = 30
    fighter.action_economy.standard_actions = 0
    fighter.action_economy.bonus_actions = 0

    CombatService.start_turn(fighter)

    assert fighter.turn_done is False
    assert fighter.action_economy.movement_used == 0
    assert fighter.action_economy.standard_actions == 1
    assert fighter.action_economy.bonus_actions == 1


def test_end_turn(fighter: Character) -> None:
    """Test end_turn marks turn as done."""
    fighter.turn_done = False

    CombatService.end_turn(fighter)

    assert fighter.turn_done is True


def test_end_round(fighter: Character) -> None:
    """Test end_round restores reaction."""
    fighter.action_economy.reaction_available = False

    CombatService.end_round(fighter)

    assert fighter.action_economy.reaction_available is True


def test_end_combat_rests_abilities(fighter: Character) -> None:
    """Test end_combat calls rest on special abilities."""
    # Get Second Wind ability
    second_wind = next(a for a in fighter.special_abilities if a.name == "Second Wind")

    # Simulate using it (current_uses should be 0 initially, increases when used)
    assert second_wind.current_uses == 0
    second_wind.current_uses = 1  # Simulate one use

    # End combat should rest it
    CombatService.end_combat(fighter)

    # Should be restored to 0 (unused state)
    assert second_wind.current_uses == 0


def test_turn_lifecycle(fighter: Character) -> None:
    """Test the full turn lifecycle using CombatService."""
    fighter.turn_done = True
    fighter.action_economy.movement_used = 20

    # Start turn
    CombatService.start_turn(fighter)

    assert fighter.turn_done is False
    assert fighter.action_economy.movement_used == 0

    # End turn
    CombatService.end_turn(fighter)
    assert fighter.turn_done is True

    # End round
    fighter.action_economy.reaction_available = False
    CombatService.end_round(fighter)
    assert fighter.action_economy.reaction_available is True
