from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agent.actions.base import ActionType, StandardAction
from agent.effects.status_effects.collection import Dodge
from agent.models.enums import TargetingType
from agent.services.effect_service import EffectService

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class DodgeAction(StandardAction):
    id: str = "dodge"
    name: str = "Dodge"
    description: str = (
        "Prepare to dodge, giving disadvantage to all attacks targeting you until next turn. "
        "Highly valuable if HP is below 50% or surrounded by multiple enemies."
    )
    type: ActionType = ActionType.DODGE
    targeting: TargetingType = TargetingType.SELF
    breaks_stealth: bool = False

    def execute(self, actor: Character, target: Any, ctx: CombatContext) -> None:  # noqa: ARG002
        effect = Dodge.with_duration(1)
        EffectService.apply_condition(actor, effect)
