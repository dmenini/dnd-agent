"""Tests for composable action system."""

from pathlib import Path

from agent.actions.base import ActionCategory, ActionType
from agent.actions.composable import ComposableAction
from agent.actions.effects.damage import DamageEffect
from agent.actions.strategies.attack_roll import AttackRollStrategy
from agent.character.abilities import AbilityType
from agent.models.damage import DamageType
from agent.models.enums import TargetingType


def test_load_longsword_from_json() -> None:
    """Test loading longsword attack from JSON file."""
    json_path = Path(__file__).parent.parent.parent / "agent" / "actions" / "definitions" / "longsword_attack.json"

    with json_path.open() as f:
        action = ComposableAction.model_validate_json(f.read())

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


def test_load_fire_bolt_from_json() -> None:
    """Test loading fire bolt from JSON file."""
    json_path = Path(__file__).parent.parent.parent / "agent" / "actions" / "definitions" / "fire_bolt.json"

    with json_path.open() as f:
        action = ComposableAction.model_validate_json(f.read())

    assert action.id == "fire_bolt"
    assert action.name == "Fire Bolt"
    assert action.type == ActionType.CAST_SPELL

    # Check damage effect
    assert len(action.effects) == 1
    damage_effect = action.effects[0]
    assert isinstance(damage_effect, DamageEffect)
    assert damage_effect.damage_dice == "1d10"
    assert damage_effect.damage_type == DamageType.FIRE
