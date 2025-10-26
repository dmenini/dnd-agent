from agent.effects.status_effects.base import EffectType, StatusEffect, StatusEffectFeature
from agent.models.damage import DamageType
from agent.models.enums import FeatureId


class Poisoned(StatusEffect):
    """
    * Target has disadvantage on attack rolls and ability checks.
    * Target takes damage over time.
    """

    type: EffectType = EffectType.POISONED
    features: list[StatusEffectFeature] = [
        StatusEffectFeature(ref_id=FeatureId.TARGET_DISADVANTAGE),
        StatusEffectFeature(ref_id=FeatureId.DAMAGE_OVER_TIME, kwargs={"value": 1, "damage_type": DamageType.POISON}),
    ]
