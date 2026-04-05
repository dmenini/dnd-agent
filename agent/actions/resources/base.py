"""Base classes for resource consumers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from agent.character.character import Character


class ResourceConsumer(BaseModel, ABC):
    """Base class for all resource consumers.

    Resource consumers handle consuming resources when an action is used.
    """

    @abstractmethod
    def consume(self, actor: Character) -> None:
        """
        Consume resources from actor.

        Args:
            actor: Character whose resources are being consumed
        """
        raise NotImplementedError

    @abstractmethod
    def is_available(self, actor: Character) -> bool:
        """
        Check if actor has resources available.

        Args:
            actor: Character to check

        Returns:
            True if actor can afford this resource cost
        """
        raise NotImplementedError
