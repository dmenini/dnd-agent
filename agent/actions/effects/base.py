"""Base classes for effect applicators."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class EffectApplicator(BaseModel, ABC):
    """Base class for all effect applicators.

    Effect applicators apply game effects to targets (damage, healing, conditions, etc.).
    """

    @abstractmethod
    def apply(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        """
        Apply the effect.

        Args:
            actor: Character performing the action
            target: Target receiving the effect
            ctx: Combat context (may contain roll results, damage, etc.)
        """
        raise NotImplementedError
