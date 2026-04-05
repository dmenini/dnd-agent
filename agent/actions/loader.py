"""Load composable actions from JSON definitions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent.actions.composable import ComposableAction
from agent.actions.base import ActionCategory, ActionType
from agent.actions.effects.damage import DamageEffect
from agent.actions.effects.healing import HealingEffect
from agent.actions.effects.conditions import ApplyConditionsEffect, RemoveConditionsEffect
from agent.actions.resources.action_economy import ActionEconomyConsumer
from agent.actions.resources.spell_slots import SpellSlotConsumer
from agent.actions.resources.limited_uses import LimitedUsesConsumer
from agent.actions.strategies.attack_roll import AttackRollStrategy
from agent.actions.strategies.saving_throw import SavingThrowStrategy
from agent.actions.strategies.auto_success import AutoSuccessStrategy
from agent.character.abilities import AbilityType
from agent.character.resources import SpellLevel
from agent.equipment.weapons import WeaponType
from agent.models.damage import DamageType
from agent.models.enums import TargetingType


class ActionLoader:
    """Factory for loading ComposableAction from JSON data."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ComposableAction:
        """
        Load ComposableAction from dictionary.

        Args:
            data: Dictionary representation of action

        Returns:
            ComposableAction instance
        """
        # Parse resolution strategy
        resolution_data = data["resolution"]
        resolution = ActionLoader._parse_resolution(resolution_data)

        # Parse effects
        effects_data = data.get("effects", [])
        effects = [ActionLoader._parse_effect(e) for e in effects_data]

        # Parse resources
        resources_data = data.get("resources", [])
        resources = [ActionLoader._parse_resource(r) for r in resources_data]

        # Create action
        return ComposableAction(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            type=ActionType(data["type"]),
            category=ActionCategory(data["category"]),
            targeting=TargetingType(data["targeting"]),
            range=data["range"],
            hits=data.get("hits", 1),
            resolution=resolution,
            effects=effects,
            resources=resources,
            metadata=data.get("metadata", {}),
        )

    @staticmethod
    def from_json(json_str: str) -> ComposableAction:
        """Load ComposableAction from JSON string."""
        data = json.loads(json_str)
        return ActionLoader.from_dict(data)

    @staticmethod
    def from_file(path: str | Path) -> ComposableAction:
        """Load ComposableAction from JSON file."""
        with open(path) as f:
            data = json.load(f)
        return ActionLoader.from_dict(data)

    @staticmethod
    def _parse_resolution(data: dict[str, Any]) -> Any:
        """Parse resolution strategy from dict."""
        strategy_type = data["type"]

        if strategy_type == "attack_roll":
            return AttackRollStrategy(
                ability=AbilityType(data["ability"]),
                weapon_type=WeaponType(data["weapon_type"])
            )
        elif strategy_type == "saving_throw":
            return SavingThrowStrategy(
                ability=AbilityType(data["ability"]),
                use_spell_dc=data.get("use_spell_dc", True)
            )
        elif strategy_type == "auto_success":
            return AutoSuccessStrategy()
        else:
            raise ValueError(f"Unknown resolution type: {strategy_type}")

    @staticmethod
    def _parse_effect(data: dict[str, Any]) -> Any:
        """Parse effect applicator from dict."""
        effect_type = data["type"]

        if effect_type == "damage":
            return DamageEffect(
                damage_dice=data["damage_dice"],
                damage_type=DamageType(data["damage_type"]),
                ability=AbilityType(data["ability"]) if "ability" in data and data["ability"] is not None else None,
                half_on_save=data.get("half_on_save", False)
            )
        elif effect_type == "healing":
            return HealingEffect(
                heal_dice=data["heal_dice"],
                ability=AbilityType(data["ability"]) if "ability" in data and data["ability"] is not None else None
            )
        elif effect_type == "apply_conditions":
            # Support both string references and full StatusEffect objects
            from agent.effects.status_effects.registry import StatusEffectRegistry

            conditions = []
            for cond in data.get("conditions", []):
                if isinstance(cond, str):
                    # String reference - look up in registry
                    conditions.append(StatusEffectRegistry.get(cond))
                else:
                    # Full StatusEffect object (not yet supported)
                    raise NotImplementedError("Full StatusEffect objects not yet supported in JSON")

            return ApplyConditionsEffect(conditions=conditions)
        elif effect_type == "remove_conditions":
            from agent.effects.status_effects.base import StatusType

            # Convert string condition types to StatusType enum
            condition_types = []
            for cond_type in data.get("condition_types", []):
                if isinstance(cond_type, str):
                    condition_types.append(StatusType(cond_type.lower()))
                else:
                    condition_types.append(cond_type)

            return RemoveConditionsEffect(condition_types=condition_types)
        else:
            raise ValueError(f"Unknown effect type: {effect_type}")

    @staticmethod
    def _parse_resource(data: dict[str, Any]) -> Any:
        """Parse resource consumer from dict."""
        resource_type = data["type"]

        if resource_type == "action_economy":
            return ActionEconomyConsumer(
                category=ActionCategory(data["category"]),
                action_type=ActionType(data.get("action_type", "attack")),
                breaks_stealth=data.get("breaks_stealth", True)
            )
        elif resource_type == "spell_slot":
            return SpellSlotConsumer(
                level=SpellLevel(data["level"])
            )
        elif resource_type == "limited_uses":
            return LimitedUsesConsumer(
                resource_name=data["resource_name"]
            )
        else:
            raise ValueError(f"Unknown resource type: {resource_type}")


class ActionRegistry:
    """Global registry for composable actions."""

    _actions: dict[str, ComposableAction] = {}

    @classmethod
    def register(cls, action: ComposableAction) -> None:
        """Register an action."""
        cls._actions[action.id] = action

    @classmethod
    def get(cls, action_id: str) -> ComposableAction | None:
        """Get action by ID."""
        return cls._actions.get(action_id)

    @classmethod
    def load_directory(cls, directory: str | Path) -> None:
        """Load all JSON files from directory."""
        path = Path(directory)
        for json_file in path.glob("*.json"):
            action = ActionLoader.from_file(json_file)
            cls.register(action)

    @classmethod
    def list_all(cls) -> list[str]:
        """List all registered action IDs."""
        return list(cls._actions.keys())
