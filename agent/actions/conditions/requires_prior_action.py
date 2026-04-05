"""Condition requiring a prior action type on this turn."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from agent.actions.base import ActionType
from agent.actions.conditions.base import AvailabilityCondition

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class RequiresPriorActionCondition(AvailabilityCondition):
    """Requires that a specific action type was used this turn.

    Used for:
    - War Priest: only after Attack action
    - Extra Attack features that require Main Attack first
    - Combo abilities that chain from other actions
    """

    type: Literal["requires_prior_action"] = "requires_prior_action"
    action_type: ActionType

    def is_available(self, actor: Character, ctx: CombatContext | None = None) -> bool:
        """Check if the required action was used this turn."""
        return actor.action_economy.last_standard_action == self.action_type
