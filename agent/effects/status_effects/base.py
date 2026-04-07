from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Literal, Self

from pydantic import BaseModel, Field

from agent.character.abilities import AbilityType
from agent.effects.base import ModifierTrait, Trait

if TYPE_CHECKING:
    from agent.character.character import Character


class StatusType(str, Enum):
    BLESSED = "blessed"
    BLINDED = "blinded"
    CUSTOM = "custom"
    DEAFENED = "deafened"
    DIVINE_FAVORED = "divine_favored"
    DODGING = "dodging"
    ENRAGED = "enraged"
    HASTED = "hasted"
    LETHARGIC = "lethargic"
    MAGIC_WEAPON = "magic_weapon"
    PARALYZED = "paralyzed"
    POISONED = "poisoned"
    SHIELDED_BY_FAITH = "shielded_by_faith"
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
        """Return a copy of this effect with a different duration."""
        return self.model_copy(update={"duration": duration})

    def on_apply(self, target: Character) -> None:
        """Call when the effect is first applied."""
        from agent.services.effect_service import EffectService  # noqa:PLC0415
        from agent.services.trait_service import TraitService  # noqa:PLC0415

        for trait in self.traits:
            TraitService.register_passive(target, trait)

        # Break concentration on incapacitating effects
        if self.type in [StatusType.STUNNED, StatusType.PARALYZED] and target.concentrating_on:
            EffectService.remove_condition(target, target.concentrating_on.type)
            target.log_event(f"{target.name} loses concentration due to {self.type.value}!")
            target.concentrating_on = None

    def on_expire(self, target: Character) -> None:
        """Call when the effect is removed."""
        from agent.services.trait_service import TraitService  # noqa:PLC0415

        for trait in self.traits:
            TraitService.unregister_passive(target, feature_id=trait.feature_id, source_id=self.type.value)

        # Clear concentration tracking if this was the concentrated effect
        if target.concentrating_on and target.concentrating_on.type == self.type:
            target.concentrating_on = None

    def is_expired(self) -> bool:
        return self.duration <= 0

    def __str__(self) -> str:
        return f"{self.type.value} ({self.duration} turns left)"
