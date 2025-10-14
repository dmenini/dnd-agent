from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agent.actions.base import Action, ActionCategory, ActionType
from agent.effects.dodge import Dodge
from agent.models.enums import TargetingType

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
        effect = Dodge(duration=1)
        actor.apply_status(effect)
        return f" {actor.name} prepares to dodge."
