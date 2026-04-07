"""Action economy resource consumer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from agent.actions.base import ActionCategory, ActionType
from agent.actions.resources.base import ResourceConsumer
from agent.services.visibility_service import VisibilityService

if TYPE_CHECKING:
    from agent.character.character import Character


class ActionEconomyConsumer(ResourceConsumer):
    """Consume action economy (standard/bonus/reaction/movement).

    This is used by almost every action to consume the appropriate action type.

    Examples:
        Standard attack:
            {"type": "action_economy", "category": "standard", "action_type": "attack"}
        Bonus action spell:
            {"type": "action_economy", "category": "bonus", "action_type": "cast_spell"}
        Reaction:
            {"type": "action_economy", "category": "reaction", "action_type": "special"}
    """

    type: Literal["action_economy"] = "action_economy"
    category: ActionCategory = Field(
        description="Action category to consume",
    )
    action_type: ActionType = Field(
        description="Type of action being performed",
    )
    breaks_stealth: bool = Field(
        default=True,
        description="If true, using this action breaks stealth/hiding",
    )

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
