from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel

from agent.character.stats import StatType
from agent.effects.registry import TraitRegistry
from agent.models.enums import FeatureId

if TYPE_CHECKING:
    from agent.character.resolvers.base import CharacterBase


class EffectType(str, Enum):
    BLESSED = "blessed"
    ENRAGED = "enraged"
    STUNNED = "stunned"
    PARALYZED = "paralyzed"
    POISONED = "poisoned"
    DODGING = "dodging"
    HASTED = "hasted"
    RESTRAINED = "restrained"
    LETHARGIC = "lethargic"
    CUSTOM = "custom"


class StatusEffectFeature(BaseModel):
    ref_id: FeatureId
    kwargs: dict = {}


class StatusEffect(BaseModel):
    type: EffectType
    duration: int
    save_stat: StatType = StatType.CON
    save_dc: int = 12  # Difficulty class
    save_mode: Literal["none", "start", "end"] = "none"
    followup: StatusEffect | None = None
    features: list[StatusEffectFeature] = []

    def on_apply(self, target: CharacterBase) -> None:
        """Call when the effect is first applied."""
        for feature in self.features:
            trait = TraitRegistry.create(
                feature_id=feature.ref_id,
                source_id=self.type.value,
                **feature.kwargs,
            )
            target.register_passive(trait=trait)

    def on_expire(self, target: CharacterBase) -> None:
        """Call when the effect is removed."""
        for feature in self.features:
            target.unregister_passive(feature_id=feature.ref_id, source_id=self.type.value)

    def is_expired(self) -> bool:
        return self.duration <= 0

    def __str__(self) -> str:
        return f"{self.type.value} ({self.duration} turns left)"
