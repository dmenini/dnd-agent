from typing import Any

from agent.effects.base import EffectType, StatusEffect
from agent.effects.registry import TraitRegistry
from agent.jobs.feature import FeatureId
from agent.models.damage import DamageType


class Poisoned(StatusEffect):
    """
    * Target has disadvantage on attack rolls and ability checks.
    * Target takes damage over time.
    """

    type: EffectType = EffectType.POISONED
    damage: int = 1

    def model_post_init(self, _: Any) -> None:
        self._traits = [
            TraitRegistry.create(FeatureId.TARGET_DISADVANTAGE),
            TraitRegistry.create(FeatureId.DAMAGE_OVER_TIME, value=self.damage, damage_type=DamageType.POISON),
        ]
