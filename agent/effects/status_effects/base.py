from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Literal, Self

from pydantic import BaseModel, Field

from agent.character.abilities import AbilityType
from agent.effects.base import ModifierTrait, Trait

if TYPE_CHECKING:
    from agent.character.resolvers.base import CharacterBase


class StatusType(str, Enum):
    BLESSED = "blessed"
    BLINDED = "blinded"
    CUSTOM = "custom"
    DEAFENED = "deafened"
    DODGING = "dodging"
    ENRAGED = "enraged"
    HASTED = "hasted"
    LETHARGIC = "lethargic"
    PARALYZED = "paralyzed"
    POISONED = "poisoned"
    STUNNED = "stunned"
    RESTRAINED = "restrained"


class StatusEffect(BaseModel):
    type: StatusType
    duration: int
    save_ability: AbilityType = AbilityType.CON
    save_dc: int = 12  # Difficulty class
    save_mode: Literal["none", "start", "end"] = "none"
    followup: StatusEffect | None = None
    traits: list[Trait | ModifierTrait] = Field(default_factory=list)

    def with_duration(self, duration: int) -> Self:
        self.duration = duration
        return self

    def on_apply(self, target: CharacterBase) -> None:
        """Call when the effect is first applied."""
        for trait in self.traits:
            target.register_passive(trait=trait)

    def on_expire(self, target: CharacterBase) -> None:
        """Call when the effect is removed."""
        for trait in self.traits:
            target.unregister_passive(feature_id=trait.feature_id, source_id=self.type.value)

    def is_expired(self) -> bool:
        return self.duration <= 0

    def __str__(self) -> str:
        return f"{self.type.value} ({self.duration} turns left)"
