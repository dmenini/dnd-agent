from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import PrivateAttr

from agent.actions.base import ActionType, StandardAction
from agent.character.resources import ActionEconomy
from agent.models.enums import TargetingType

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext
    from agent.models.position import Position


class DashAction(StandardAction):
    id: str = "dash"
    name: str = "Dash"
    description: str = "Dash on the map to a new position within double the range."
    type: ActionType = ActionType.DASH
    targeting: TargetingType = TargetingType.AREA
    range: float
    breaks_stealth: bool = False

    _distance: float = PrivateAttr(default=0)

    def model_post_init(self, _: Any, /) -> None:
        self.range = self.range * 2

    def is_available(self, action_economy: ActionEconomy) -> bool:
        # Here we simply check that the actor has movement available, as we still don't know the target position
        return action_economy.can_use_standard(self.type) and action_economy.can_move(distance=self.range)

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
        """Consume standard action point and movement."""
        super().finalize(actor)
        movement_cost = self._distance / 2
        actor.action_economy.use_movement(distance=movement_cost)
        self._distance = 0
