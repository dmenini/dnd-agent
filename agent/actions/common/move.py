from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import PrivateAttr

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

    _distance: float = PrivateAttr(default=0)

    def is_available(self, action_economy: ActionEconomy) -> bool:
        return action_economy.can_move(distance=self.range)

    def execute(self, actor: Character, target: Position, ctx: CombatContext) -> None:
        if not ctx.map:
            raise ValueError

        dist = ctx.map.distance(start=actor.pos, end=target)
        if dist is None:
            msg = "Target position cannot be reached"
            raise ValueError(msg)

        self._distance = dist
        actor.move(target)

    def finalize(self, actor: Character) -> None:
        """Consume movement."""
        movement_cost = self._distance
        actor.action_economy.use_movement(distance=movement_cost)
        self._distance = 0
