from __future__ import annotations

from typing import TYPE_CHECKING

from agent.actions.base import Action, ActionCategory, ActionEconomy, ActionType
from agent.models.enums import TargetingType

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.position import Position


class DashAction(Action):
    """Option shown to the Agent"""

    id: str = "dash"
    name: str = "Dash"
    description: str = "Dash on the map to a new position within double the range."
    action_type: ActionType = ActionType.DASH
    category: ActionCategory = ActionCategory.STANDARD

    targeting: TargetingType = TargetingType.SELF
    range: float

    def is_available(self, action_economy: ActionEconomy) -> bool:
        return action_economy.standard_actions > 0 and action_economy.movement_available

    def execute(self, actor: Character, target: Position) -> str:
        actor.move(target, dash=True)
        return f" {actor.name} moves to position {target}."

    def finalize(self, actor: Character) -> None:
        """Consume standard action point and movement."""
        super().finalize(actor)

        if not actor.action_economy.movement_available:
            raise ValueError("Already moved")
        actor.action_economy.movement_available = False
