"""Tests for DM action builder tool."""

import json

import pytest
from pydantic_core import ValidationError

from agent.actions.base import ActionCategory, ActionType
from agent.actions.composable import ComposableAction
from agent.actions.effects.damage import DamageEffect
from agent.actions.effects.healing import HealingEffect
from agent.actions.resources.action_economy import ActionEconomyConsumer
from agent.actions.strategies.attack_roll import AttackRollStrategy
from agent.actions.strategies.auto_success import AutoSuccessStrategy
from agent.actions.strategies.saving_throw import SavingThrowStrategy
from agent.ai.dm.action_builder_tool import create_custom_action
from agent.character.abilities import AbilityType
from agent.equipment.weapons import WeaponType
from agent.models.damage import DamageType
from agent.models.enums import TargetingType


def test_create_damage_action() -> None:
    """Test creating a simple damage action."""
    action = ComposableAction(
        id="test_fireball",
        name="Fireball",
        description="Hurl a ball of fire",
        type=ActionType.CAST_SPELL,
        category=ActionCategory.STANDARD,
        targeting=TargetingType.MULTI,
        range=60.0,
        hits=1,
        resolution=SavingThrowStrategy(ability=AbilityType.DEX, use_spell_dc=True),
        effects=[DamageEffect(damage_dice="8d6", damage_type=DamageType.FIRE, ability=None, half_on_save=False)],
        resources=[ActionEconomyConsumer(category=ActionCategory.STANDARD, action_type=ActionType.CAST_SPELL)],
        level_required=5,
    )

    result = create_custom_action.invoke({"action": action})

    assert "Action created successfully" in result

    # Parse the JSON output
    json_str = result.split("\n\n", 1)[1]
    action_data = json.loads(json_str)

    assert action_data["id"] == "test_fireball"
    assert action_data["name"] == "Fireball"
    assert action_data["type"] == "cast_spell"
    assert action_data["category"] == "standard"
    assert action_data["targeting"] == "multi"
    assert action_data["range"] == 60.0
    assert action_data["resolution"]["type"] == "saving_throw"
    assert action_data["resolution"]["ability"] == "dexterity"
    assert len(action_data["effects"]) == 1
    assert action_data["effects"][0]["type"] == "damage"
    assert action_data["effects"][0]["damage_dice"] == "8d6"
    assert action_data["effects"][0]["damage_type"] == "fire"

    # Verify it can be loaded back as ComposableAction
    parsed_action = ComposableAction.model_validate(action_data)
    assert parsed_action.id == "test_fireball"


def test_create_healing_action() -> None:
    """Test creating a healing action."""
    action = ComposableAction(
        id="test_healing_potion",
        name="Healing Potion",
        description="Drink to restore HP",
        type=ActionType.SPECIAL,
        category=ActionCategory.BONUS,
        targeting=TargetingType.SELF,
        range=0.0,
        hits=1,
        resolution=AutoSuccessStrategy(),
        effects=[HealingEffect(heal_dice="2d4+2", ability=None)],
        resources=[ActionEconomyConsumer(category=ActionCategory.BONUS, action_type=ActionType.SPECIAL)],
        level_required=1,
    )

    result = create_custom_action.invoke({"action": action})

    assert "Action created successfully" in result

    json_str = result.split("\n\n", 1)[1]
    action_data = json.loads(json_str)

    assert action_data["id"] == "test_healing_potion"
    assert action_data["resolution"]["type"] == "auto_success"
    assert len(action_data["effects"]) == 1
    assert action_data["effects"][0]["type"] == "healing"
    assert action_data["effects"][0]["heal_dice"] == "2d4+2"


def test_create_attack_action() -> None:
    """Test creating an attack roll action."""
    action = ComposableAction(
        id="test_cleave",
        name="Cleave",
        description="Powerful strike hitting multiple foes",
        type=ActionType.ATTACK,
        category=ActionCategory.STANDARD,
        targeting=TargetingType.MULTI,
        range=1.5,
        hits=2,
        resolution=AttackRollStrategy(ability=AbilityType.STR, weapon_type=WeaponType.MARTIAL_MELEE),
        effects=[
            DamageEffect(
                damage_dice="1d12+5", damage_type=DamageType.SLASHING, ability=AbilityType.STR, half_on_save=False
            )
        ],
        resources=[ActionEconomyConsumer(category=ActionCategory.STANDARD, action_type=ActionType.ATTACK)],
        level_required=1,
    )

    result = create_custom_action.invoke({"action": action})

    assert "Action created successfully" in result

    json_str = result.split("\n\n", 1)[1]
    action_data = json.loads(json_str)

    assert action_data["id"] == "test_cleave"
    assert action_data["hits"] == 2
    assert action_data["resolution"]["type"] == "attack_roll"
    assert action_data["resolution"]["ability"] == "strength"
    assert action_data["resolution"]["weapon_type"] == "martial_melee"


def test_create_action_with_damage_and_healing() -> None:
    """Test creating action with both damage and healing."""
    action = ComposableAction(
        id="test_vampiric_touch",
        name="Vampiric Touch",
        description="Drain life from target",
        type=ActionType.CAST_SPELL,
        category=ActionCategory.STANDARD,
        targeting=TargetingType.SINGLE,
        range=1.5,
        hits=1,
        resolution=AttackRollStrategy(ability=AbilityType.INT, weapon_type=WeaponType.MAGIC),
        effects=[
            DamageEffect(damage_dice="3d6", damage_type=DamageType.NECROTIC, ability=None, half_on_save=False),
            HealingEffect(heal_dice="3d6", ability=None),
        ],
        resources=[ActionEconomyConsumer(category=ActionCategory.STANDARD, action_type=ActionType.CAST_SPELL)],
        level_required=3,
    )

    result = create_custom_action.invoke({"action": action})

    assert "Action created successfully" in result

    json_str = result.split("\n\n", 1)[1]
    action_data = json.loads(json_str)

    # Should have both damage and healing effects
    assert len(action_data["effects"]) == 2
    effect_types = {e["type"] for e in action_data["effects"]}
    assert "damage" in effect_types
    assert "healing" in effect_types


def test_missing_required_params_for_attack() -> None:
    """Test that attack_roll requires ability and weapon_type."""
    action_dict = {
        "id": "test_bad_attack",
        "name": "Bad Attack",
        "description": "Missing params",
        "type": "attack",
        "category": "standard",
        "targeting": "single",
        "range": 1.5,
        "hits": 1,
        "resolution": {"type": "attack_roll"},  # Missing ability and weapon_type
        "effects": [
            {
                "type": "damage",
                "damage_dice": "1d8",
                "damage_type": "slashing",
                "ability": None,
                "half_on_save": False,
            }
        ],
        "resources": [
            {"type": "action_economy", "category": "standard", "action_type": "attack", "breaks_stealth": True}
        ],
        "level": 1,
    }
    with pytest.raises(ValidationError, match="adjcn"):
        ComposableAction.model_validate(action_dict)


def test_missing_required_params_for_save() -> None:
    """Test that saving_throw requires save_ability."""

    action_dict = {
        "id": "test_bad_save",
        "name": "Bad Save",
        "description": "Missing params",
        "type": "cast_spell",
        "category": "standard",
        "targeting": "multi",
        "range": 30.0,
        "hits": 1,
        "resolution": {"type": "saving_throw"},  # Missing ability
        "effects": [
            {"type": "damage", "damage_dice": "6d6", "damage_type": "fire", "ability": None, "half_on_save": False}
        ],
        "resources": [
            {"type": "action_economy", "category": "standard", "action_type": "cast_spell", "breaks_stealth": True}
        ],
        "level": 3,
    }

    with pytest.raises(ValidationError, match="saving_throw.ability\n  Field required"):
        ComposableAction.model_validate(action_dict)
