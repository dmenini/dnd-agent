from __future__ import annotations

from typing import TYPE_CHECKING

from agent.actions.base import Action, ActionCategory, ActionEconomy, ActionType
from agent.models.enums import TargetingType

if TYPE_CHECKING:
    from agent.character.character import Character


class WaitAction(Action):
    """Option shown to the Agent"""

    id: str = "wait"
    name: str = "Wait"
    description: str = "Pass turn."
    action_type: ActionType = ActionType.WAIT
    category: ActionCategory = ActionCategory.STANDARD

    targeting: TargetingType = TargetingType.SELF

    def is_available(self, action_economy: ActionEconomy) -> bool:
        return action_economy.standard_actions > 0 or action_economy.movement_available

    def execute(self, actor: Character, _: Character) -> None:
        return actor.log_event(f"{actor.name} passes turn")

    def finalize(self, actor: Character) -> None:
        """Consume all resources."""
        actor.action_economy.standard_actions = 0
        actor.action_economy.bonus_actions = 0
        actor.action_economy.movement_available = False
        actor.action_economy.reaction_available = False
