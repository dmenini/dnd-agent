"""Condition requiring minimum resource threshold."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from agent.actions.conditions.base import AvailabilityCondition

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class ResourceThresholdCondition(AvailabilityCondition):
    """Requires a minimum amount of a resource.

    Used for:
    - Ki abilities: require minimum ki points
    - Sorcery points: require minimum points
    - Custom resource gating
    """

    type: Literal["resource_threshold"] = "resource_threshold"
    resource_name: str
    min_amount: int

    def is_available(self, actor: Character, ctx: CombatContext | None = None) -> bool:  # noqa: ARG002
        """Check if actor has enough of the resource."""
        resource = actor.limited_resources.get(self.resource_name)
        if resource is None:
            return False  # Resource doesn't exist

        available = resource.max_uses - resource.current_uses
        return available >= self.min_amount
