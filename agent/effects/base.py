from __future__ import annotations

import uuid
from enum import Enum
from typing import TYPE_CHECKING, Literal

from anthropic import BaseModel
from pydantic import PrivateAttr

from agent.character.stats import StatType

if TYPE_CHECKING:
    from agent.character.resolvers.base import CharacterBase


class Priority:
    HIGH: int = -100  # Execute first
    MEDIUM: int = 0
    LOW: int = 100  # Execute last


class EffectType(str, Enum):
    STUNNED = "stunned"
    PARALYZED = "paralyzed"
    POISONED = "poisoned"
    DODGING = "dodging"
    HASTED = "hasted"
    RESTRAINED = "restrained"
    LETHARGIC = "lethargic"
    CUSTOM = "custom"


class Trait(BaseModel):
    source: str = ""
    _id: str = PrivateAttr(default=str(uuid.uuid4()))
    _priority: int = PrivateAttr(default=Priority.MEDIUM)

    @property
    def priority(self) -> int:
        return self._priority

    def on_apply(self, target: CharacterBase) -> None:
        """Call when the effect is first applied."""

    def on_expire(self, target: CharacterBase) -> None:
        """Call when the effect is first applied."""
        target.unregister_modifier(self._id)
        target.unregister_listeners(self._id)


class StatusEffect(Trait):
    type: EffectType
    duration: int
    save_stat: StatType = StatType.CON
    save_dc: int = 12  # Difficulty class
    save_mode: Literal["none", "start", "end"] = "none"
    followup: StatusEffect | None = None

    _traits: list[Trait] = PrivateAttr(default_factory=list)

    @property
    def traits(self) -> list[Trait]:
        return sorted(self._traits, key=lambda t: t.priority)

    def on_apply(self, target: CharacterBase) -> None:
        """Call when the effect is first applied."""
        super().on_apply(target)
        for trait in self.traits:
            trait.source = self.__class__.__name__
            trait.on_apply(target)

    def on_expire(self, target: CharacterBase) -> None:
        """Call when the effect is first applied."""
        super().on_expire(target)
        for trait in self.traits:
            trait.on_expire(target)

    def is_expired(self) -> bool:
        return self.duration <= 0

    def __str__(self) -> str:
        return f"{self.type.value} ({self.duration} turns left)"
