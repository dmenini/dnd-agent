"""Condition restricting action based on equipped armor."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from agent.actions.conditions.base import AvailabilityCondition
from agent.equipment.armor import ArmorType

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class ArmorRestrictionCondition(AvailabilityCondition):
    """Restricts action usage based on equipped armor type.

    Used for:
    - Rage: cannot be used in heavy armor
    - Monk abilities: require no armor or light armor
    - Stealth abilities: disadvantage in heavy armor
    """

    type: Literal["armor_restriction"] = "armor_restriction"
    forbidden_types: list[ArmorType]

    def is_available(self, actor: Character, ctx: CombatContext | None = None) -> bool:  # noqa: ARG002
        """Check if actor's armor is allowed."""
        if not actor.equipment.armor:
            return True  # No armor is always allowed
        return actor.equipment.armor.armor_type not in self.forbidden_types
