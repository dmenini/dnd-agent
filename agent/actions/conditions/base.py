"""Base class for availability conditions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class AvailabilityCondition(BaseModel, ABC):
    """Base class for conditions that determine if an action can be used.

    Availability conditions extend the basic resource/action economy checks
    with custom logic like:
    - Armor restrictions (Rage not in heavy armor)
    - Prior action requirements (War Priest after Attack)
    - Resource thresholds (minimum resources needed)
    - Environmental conditions (terrain, weather, etc.)
    """

    type: str

    @abstractmethod
    def is_available(self, actor: Character, ctx: CombatContext | None = None) -> bool:
        """Check if the condition is satisfied.

        Args:
            actor: The character attempting to use the action
            ctx: Optional combat context

        Returns:
            True if the action can be used, False otherwise
        """
        raise NotImplementedError
