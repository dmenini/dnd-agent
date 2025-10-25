from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from anthropic import BaseModel
from pydantic import PrivateAttr

from agent.models.enums import FeatureId

if TYPE_CHECKING:

    from agent.character.resolvers.base import CharacterBase


class Priority:
    HIGH: int = -100  # Execute first
    MEDIUM: int = 0
    LOW: int = 100  # Execute last


class Trait(BaseModel):
    name: str = ""
    description: str = ""
    feature: FeatureId
    source_id: str = ""
    _id: str = PrivateAttr(default=str(uuid.uuid4()))
    _priority: int = PrivateAttr(default=Priority.MEDIUM)

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def id(self) -> str:
        return self._id

    def on_apply(self, target: CharacterBase) -> None:
        """Call when the effect is first applied."""

    def on_expire(self, target: CharacterBase) -> None:
        """Call when the effect is first applied."""
        target.unregister_modifier(self._id)
        target.unregister_listeners(self._id)
