"""Tests for composable action system."""

import pytest
from pathlib import Path

from agent.actions.loader import ActionLoader, ActionRegistry
from agent.actions.composable import ComposableAction
from agent.actions.base import ActionCategory, ActionType
from agent.actions.strategies.attack_roll import AttackRollStrategy
from agent.actions.effects.damage import DamageEffect
from agent.character.abilities import AbilityType
from agent.models.damage import DamageType
from agent.models.enums import TargetingType


def test_load_longsword_from_json():
    """Test loading longsword attack from JSON file."""
    json_path = Path(__file__).parent.parent.parent / "agent" / "actions" / "definitions" / "longsword_attack.json"

    action = ActionLoader.from_file(json_path)

    assert action.id == "longsword_attack"
    assert action.name == "Longsword Attack"
    assert action.type == ActionType.ATTACK
    assert action.category == ActionCategory.STANDARD
    assert action.targeting == TargetingType.SINGLE
    assert action.range == 1.5

    # Check resolution
    assert isinstance(action.resolution, AttackRollStrategy)
    assert action.resolution.ability == AbilityType.STR

    # Check effects
    assert len(action.effects) == 1
    assert isinstance(action.effects[0], DamageEffect)
    assert action.effects[0].damage_dice == "1d8"
    assert action.effects[0].damage_type == DamageType.SLASHING


def test_load_fire_bolt_from_json():
    """Test loading fire bolt from JSON file."""
    json_path = Path(__file__).parent.parent.parent / "agent" / "actions" / "definitions" / "fire_bolt.json"

    action = ActionLoader.from_file(json_path)

    assert action.id == "fire_bolt"
    assert action.name == "Fire Bolt"
    assert action.type == ActionType.CAST_SPELL

    # Check damage effect
    assert len(action.effects) == 1
    damage_effect = action.effects[0]
    assert isinstance(damage_effect, DamageEffect)
    assert damage_effect.damage_dice == "1d10"
    assert damage_effect.damage_type == DamageType.FIRE


def test_action_registry():
    """Test action registry."""
    json_path = Path(__file__).parent.parent.parent / "agent" / "actions" / "definitions" / "longsword_attack.json"

    action = ActionLoader.from_file(json_path)
    ActionRegistry.register(action)

    retrieved = ActionRegistry.get("longsword_attack")
    assert retrieved is not None
    assert retrieved.name == "Longsword Attack"


def test_load_directory():
    """Test loading all actions from directory."""
    definitions_dir = Path(__file__).parent.parent.parent / "agent" / "actions" / "definitions"

    ActionRegistry.load_directory(definitions_dir)

    action_ids = ActionRegistry.list_all()
    assert "longsword_attack" in action_ids
    assert "fire_bolt" in action_ids
    assert "cure_wounds" in action_ids
