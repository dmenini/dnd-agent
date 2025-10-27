from __future__ import annotations

from typing import TYPE_CHECKING

from agent.actions.base import ActionType, StandardAction
from agent.character.resources import ActionEconomy
from agent.models.enums import TargetingType

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class WaitAction(StandardAction):
    id: str = "wait"
    name: str = "Wait"
    description: str = "Pass turn."
    type: ActionType = ActionType.WAIT
    targeting: TargetingType = TargetingType.SELF
    breaks_stealth: bool = False

    def is_available(self, action_economy: ActionEconomy) -> bool:
        return action_economy.can_use_standard() or action_economy.can_move(distance=0)

    def execute(self, actor: Character, target: Character, ctx: CombatContext) -> None:  # noqa: ARG002
        return

    def finalize(self, actor: Character) -> None:
        """Consume all resources."""
        actor.action_economy.use_movement(distance=actor.current_speed)
        actor.action_economy.use_standard()
        actor.action_economy.use_bonus()
        actor.action_economy.use_reaction()
