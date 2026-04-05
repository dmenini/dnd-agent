"""Auto-success resolution strategy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from agent.actions.strategies.base import ResolutionStrategy

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class AutoSuccessStrategy(ResolutionStrategy):
    """Always succeeds.

    Used for:
    - Healing spells (no roll needed)
    - Buff spells (always apply to willing targets)
    - Utility actions (opening doors, searching, etc.)
    - Self-targeted abilities (Rage, Second Wind)

    No rolls, no checks - just apply the effects.
    """

    def resolve(self, actor: Character, target: Character, ctx: CombatContext) -> bool:  # noqa: ARG002
        """Always return True."""
        return True
