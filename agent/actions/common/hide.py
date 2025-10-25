from typing import Any

from agent.actions.base import Action, ActionCategory, ActionType
from agent.character.character import Character
from agent.models.context import CombatContext
from agent.models.enums import TargetingType


class HideAction(Action):
    id: str = "hide"
    name: str = "Hide"
    description: str = "Hide."
    action_type: ActionType = ActionType.HIDE
    category: ActionCategory = ActionCategory.STANDARD
    targeting: TargetingType = TargetingType.SELF
    range: float = 1

    def execute(self, actor: Character, target: Any, ctx: CombatContext) -> None:  # noqa: ARG002
        roll = actor.stealth_roll()
        actor.stealth_value = roll.total
