from __future__ import annotations

from typing import TYPE_CHECKING

from agent.actions.base import Action, ActionCategory, ActionType
from agent.character.resources import ActionEconomy
from agent.models.enums import TargetingType

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext
    from agent.models.position import Position


class MovementAction(Action):
    id: str = "move"
    name: str = "Movement"
    description: str = "Move on the map to a new position within the range."
    action_type: ActionType = ActionType.MOVE
    category: ActionCategory = ActionCategory.MOVEMENT

    targeting: TargetingType = TargetingType.AREA
    range: float

    def is_available(self, action_economy: ActionEconomy) -> bool:
        return action_economy.can_move(distance=self.range)

    def execute(self, actor: Character, target: Position, ctx: CombatContext) -> None:  # noqa: ARG002
        actor.move(target)

    def finalize(self, actor: Character) -> None:
        """Consume movement."""
        actor.action_economy.use_movement(distance=self.range)
