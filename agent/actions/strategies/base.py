"""Base classes for resolution strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class ResolutionStrategy(BaseModel, ABC):
    """Base class for all resolution strategies.

    Resolution strategies determine whether an action succeeds or fails.
    """

    apply_on_failure: bool = False

    @abstractmethod
    def resolve(self, actor: Character, target: Character, ctx: CombatContext) -> bool:
        """
        Determine if the action succeeds.

        Args:
            actor: Character performing the action
            target: Target of the action
            ctx: Combat context (stores roll results, hit status, etc.)

        Returns:
            True if action succeeds and effects should apply, False otherwise
        """
        raise NotImplementedError
