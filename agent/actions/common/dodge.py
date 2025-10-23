from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agent.actions.base import Action, ActionCategory, ActionType
from agent.effects.status_effects.dodge import Dodge
from agent.models.enums import TargetingType

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class DodgeAction(Action):
    id: str = "dodge"
    name: str = "Dodge"
    description: str = "Prepare to dodge in the next turn."
    action_type: ActionType = ActionType.DODGE
    category: ActionCategory = ActionCategory.STANDARD

    targeting: TargetingType = TargetingType.SELF

    def execute(self, actor: Character, target: Any, ctx: CombatContext) -> None:  # noqa: ARG002
        effect = Dodge(duration=1)
        actor.apply_effect(effect)
