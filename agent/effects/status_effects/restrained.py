from typing import Any

from agent.character.stats import StatType
from agent.effects.base import EffectType, StatusEffect
from agent.effects.registry import TraitRegistry
from agent.effects.traits import (
    Trait,
)
from agent.jobs.feature import FeatureId


class Restrained(StatusEffect):
    """
    * Target's speed becomes 0 -> Modeled as no movement.
    * Target can't benefit from any bonus to its speed -> Modeled as no movement.
    * Attack rolls against the target have advantage.
    * Target attack rolls have disadvantage.
    * Target has disadvantage on Dexterity saving throws.
    """

    type: EffectType = EffectType.RESTRAINED

    def model_post_init(self, _: Any) -> None:
        self._traits: list[Trait] = [
            TraitRegistry.create(FeatureId.CANNOT_MOVE),
            TraitRegistry.create(FeatureId.SAVE_DISADVANTAGE, stat=StatType.DEX),
            TraitRegistry.create(FeatureId.ATTACKER_ADVANTAGE),
            TraitRegistry.create(FeatureId.TARGET_DISADVANTAGE),
        ]
