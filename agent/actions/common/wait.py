from __future__ import annotations

from typing import TYPE_CHECKING

from agent.actions.base import Action, ActionCategory, ActionType
from agent.character.resources import ActionEconomy
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
        return action_economy.can_use_standard() or action_economy.can_move(distance=0)

    def execute(self, actor: Character, target: Character) -> None:  # noqa: ARG002
        return

    def finalize(self, actor: Character) -> None:
        """Consume all resources."""
        actor.action_economy.use_movement(distance=0)
        actor.action_economy.use_standard()
        actor.action_economy.use_bonus()
        actor.action_economy.use_reaction()
