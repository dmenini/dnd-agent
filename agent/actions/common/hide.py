from typing import Any

from agent.actions.base import ActionType, StandardAction
from agent.character.character import Character
from agent.models.context import CombatContext
from agent.models.enums import TargetingType


class HideAction(StandardAction):
    id: str = "hide"
    name: str = "Hide"
    description: str = (
        "Attempt to become unseen by enemies, gaining advantage on attacks "
        "and avoiding being targeted until revealed. Requires being out of enemies' line of sight."
    )
    action_type: ActionType = ActionType.HIDE
    targeting: TargetingType = TargetingType.SELF
    range: float = 1
    breaks_stealth: bool = False

    def execute(self, actor: Character, target: Any, ctx: CombatContext) -> None:  # noqa: ARG002
        # TODO: Make this conditional on LoS
        actor.hide()
