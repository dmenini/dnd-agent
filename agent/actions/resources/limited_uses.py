"""Limited uses resource consumer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from agent.actions.resources.base import ResourceConsumer

if TYPE_CHECKING:
    from agent.character.character import Character


class LimitedUsesConsumer(ResourceConsumer):
    """Consume from limited-use resources.

    Used for:
    - Class features (Second Wind, Rage, Action Surge)
    - Racial abilities (Dragonborn Breath Weapon)
    - Magic items with charges

    The resource is tracked on the character by name.
    """

    resource_name: str  # e.g., "second_wind", "rage", "channel_divinity"

    def consume(self, actor: Character) -> None:
        """Consume from limited-use resource."""
        resource = actor.resources.get(self.resource_name)
        if resource:
            resource.consume()

    def is_available(self, actor: Character) -> bool:
        """Check if actor has uses remaining."""
        resource = actor.resources.get(self.resource_name)
        if not resource:
            return False  # Resource doesn't exist
        return resource.current < resource.max_uses
