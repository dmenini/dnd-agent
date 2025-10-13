from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agent.actions.base import Action, ActionCategory, ActionType
from agent.models.enums import ConditionType, TargetingType

if TYPE_CHECKING:
    from agent.models.character import Character


class DodgeAction(Action):
    """Option shown to the Agent"""

    id: str = "dodge"
    name: str = "Dodge"
    description: str = "Prepare to dodge in the next turn."
    action_type: ActionType = ActionType.DODGE
    category: ActionCategory = ActionCategory.STANDARD

    targeting: TargetingType = TargetingType.SELF

    def execute(self, actor: Character, target: Any) -> str:  # noqa: ARG002
        actor.apply_condition(cond=ConditionType.DODGING, duration=1)
        return f" {actor.name} prepares to dodge."
