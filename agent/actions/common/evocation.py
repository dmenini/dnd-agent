"""Evocation-related actions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import PrivateAttr

from agent.actions.common.move import MovementAction
from agent.models.enums import FeatureId
from agent.models.position import Position

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class RepositionEvocationAction(MovementAction):
    """Move an evocation to a new position.

    This is automatically available for all evocations (like character movement).
    """

    id: str = FeatureId.REPOSITION_EVOCATION.value
    name: str = "Reposition Evocation"
    description: str = "Move evocation to a new position within the range, or turn towards a new direction."
    evocation_name: str

    _distance: float = PrivateAttr(default=0)

    def execute(self, actor: Character, target: Position, ctx: CombatContext) -> None:
        if not ctx.map:
            raise ValueError

        dist = ctx.map.distance(start=actor.combat.pos, end=target)
        if dist is None or dist > self.range:
            msg = "Target position cannot be reached"
            raise ValueError(msg)

        self._distance = dist
        evo = next(evo for evo in actor.evocations if evo.name == self.evocation_name)
        evo.position = target

    def finalize(self, actor: Character) -> None:
        """Consume movement."""
        movement_cost = self._distance
        evo = next(evo for evo in actor.evocations if evo.name == self.evocation_name)
        evo.action_economy.use_movement(distance=movement_cost)
        self._distance = 0
