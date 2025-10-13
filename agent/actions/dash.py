from __future__ import annotations

from typing import TYPE_CHECKING

from agent.actions.base import Action, ActionEconomy
from agent.models.enums import ActionCategory, ActionType, TargetingType

if TYPE_CHECKING:
    from agent.models.character import Character


class DashAction(Action):
    """Option shown to the Agent"""

    id: str = "dash"
    name: str = "Dash"
    description: str = "Move on the map to a new position within the range."
    action_type: ActionType = ActionType.DASH
    category: ActionCategory = ActionCategory.STANDARD

    targeting: TargetingType = TargetingType.SELF
    range: float

    def is_available(self, action_economy: ActionEconomy) -> bool:
        return action_economy.standard_actions > 0 and action_economy.movement_available

    def execute(self, actor: Character, target: tuple[int, int]) -> str:
        actor.move(target, dash=True)
        return f" {actor.name} moves to position {target}."
