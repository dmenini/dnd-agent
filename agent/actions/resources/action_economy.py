"""Action economy resource consumer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from agent.actions.base import ActionCategory, ActionType
from agent.actions.resources.base import ResourceConsumer
from agent.services.visibility_service import VisibilityService

if TYPE_CHECKING:
    from agent.character.character import Character


class ActionEconomyConsumer(ResourceConsumer):
    """Consume action economy (standard/bonus/reaction/movement).

    This is used by almost every action to consume the appropriate action type.
    """

    type: Literal["action_economy"] = "action_economy"
    category: ActionCategory
    action_type: ActionType
    breaks_stealth: bool = True

    def consume(self, actor: Character) -> None:
        """Consume action economy from actor."""
        if self.category == ActionCategory.STANDARD:
            actor.action_economy.use_standard(self.action_type)
        elif self.category == ActionCategory.BONUS:
            actor.action_economy.use_bonus(self.action_type)
        elif self.category == ActionCategory.REACTION:
            actor.action_economy.use_reaction()
        elif self.category == ActionCategory.MOVEMENT:
            # Movement is handled differently (by distance, not binary)
            pass

        # Break stealth if this action makes noise/is visible
        if self.breaks_stealth and actor.is_hidden:
            VisibilityService.unhide(actor)

    def is_available(self, actor: Character) -> bool:
        """Check if actor has action economy available."""
        if self.category == ActionCategory.STANDARD:
            return actor.action_economy.can_use_standard(self.action_type)
        if self.category == ActionCategory.BONUS:
            return actor.action_economy.can_use_bonus(self.action_type)
        if self.category == ActionCategory.REACTION:
            return actor.action_economy.can_use_reaction()
        return self.category == ActionCategory.MOVEMENT  # Movement availability checked per-distance
