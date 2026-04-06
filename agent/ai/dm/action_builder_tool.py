"""Tool for DM agent to create custom actions dynamically."""

from __future__ import annotations

import json

from langchain_core.tools import tool

from agent.actions.composable import ComposableAction


@tool
def create_custom_action(action: ComposableAction) -> str:
    """
    Create a custom action for an NPC or special encounter.

    Use this tool when you need to create a unique ability for:
    - Boss monsters with special attacks
    - Environmental hazards (traps, falling rocks)
    - Magical items with active abilities
    - Narrative-driven actions

    The ComposableAction schema is fully documented with field descriptions.
    Key components:
    - Base fields define the action identity and behavior
    - Resolution strategy determines how success is calculated
    - Effects list what happens on success (damage, healing, etc.)
    - Resources list what is consumed (action economy, spell slots, etc.)

    Common patterns:
    - Attack: attack_roll resolution + damage effect
    - Spell: saving_throw resolution + damage/healing effect
    - Healing: auto_success resolution + healing effect
    - Buff/Debuff: auto_success + apply_conditions effect

    Args:
        action: ComposableAction with all required fields

    Returns:
        JSON representation of the validated action
    """
    # Use model_dump with mode='json' to avoid serialization warnings for discriminated unions
    return f"Action created successfully!\n\n{json.dumps(action.model_dump(mode='json'), indent=2)}"
