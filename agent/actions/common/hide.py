from typing import Any

from agent.actions.base import ActionType, StandardAction
from agent.character.character import Character
from agent.logs.events import Icon
from agent.models.context import CombatContext
from agent.models.enums import TargetingType


class HideAction(StandardAction):
    id: str = "hide"
    name: str = "Hide"
    description: str = (
        "Try to hide when behind obstacles or out of sight, repositioning safely. "
        "While hidden, enemies cannot target you, and your next attack gains advantage. "
        "Use strategically to flank, escape, or ambush."
    )
    action_type: ActionType = ActionType.HIDE
    targeting: TargetingType = TargetingType.SELF
    range: float = 1
    breaks_stealth: bool = False

    def execute(self, actor: Character, target: Any, ctx: CombatContext) -> None:  # noqa: ARG002
        if ctx.map is None:
            raise ValueError

        # Only allow hiding if no enemy has line of sight
        can_hide = all(not ctx.map.within_visibility_range(enemy, actor) for enemy in ctx.enemies)

        if can_hide:
            actor.hide()
        else:
            actor.log_event(f"{actor.name} cannot hide: spotted by an enemy!", icon=Icon.STEALTH)
