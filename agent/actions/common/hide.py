from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agent.actions.base import ActionType, StandardAction
from agent.logs.log_event import Icon
from agent.models.enums import TargetingType
from agent.services.visibility_service import VisibilityService

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class HideAction(StandardAction):
    id: str = "hide"
    name: str = "Hide"
    description: str = (
        "Try to hide when behind obstacles or out of sight, repositioning safely. "
        "While hidden, enemies cannot target you, and your next attack gains advantage. "
        "Use strategically to flank, escape, or ambush."
    )
    type: ActionType = ActionType.HIDE
    targeting: TargetingType = TargetingType.SELF
    range: float = 1
    breaks_stealth: bool = False

    def execute(self, actor: Character, target: Any, ctx: CombatContext) -> None:  # noqa: ARG002
        if ctx.map is None:
            raise ValueError

        # Only allow hiding if no enemy has line of sight
        can_hide = all(actor.pos not in ctx.map.get_visible_positions(enemy) for enemy in ctx.enemies)

        if can_hide:
            VisibilityService.hide(actor)
        else:
            actor.log_event(f"{actor.name} cannot hide: spotted by an enemy!", icon=Icon.STEALTH, show_ai=True)
