from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import PrivateAttr

from agent.actions.base import Action, ActionCategory, ActionType
from agent.character.resources import ActionEconomy
from agent.models.enums import FeatureId, TargetingType
from agent.services.combat_service import CombatService

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext
    from agent.models.position import Position


class MovementAction(Action):
    id: str = FeatureId.MOVE.value
    name: str = "Movement"
    description: str = "Move on the map to a new position within the range, or turn towards a new direction."
    type: ActionType = ActionType.MOVE
    category: ActionCategory = ActionCategory.MOVEMENT
    targeting: TargetingType = TargetingType.AREA
    range: float
    breaks_stealth: bool = False

    _distance: float = PrivateAttr(default=0)

    def is_available(self, action_economy: ActionEconomy) -> bool:
        return action_economy.can_move(distance=self.range)

    def execute(self, actor: Character, target: Position, ctx: CombatContext) -> None:
        if not ctx.map:
            raise ValueError

        dist = ctx.map.distance(start=actor.pos, end=target)
        if dist is None or dist > self.range:
            msg = "Target position cannot be reached"
            raise ValueError(msg)

        self._distance = dist
        CombatService.move(actor, target)

    def finalize(self, actor: Character) -> None:
        """Consume movement."""
        movement_cost = self._distance
        actor.action_economy.use_movement(distance=movement_cost)
        self._distance = 0
