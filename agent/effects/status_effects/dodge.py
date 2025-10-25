from agent.effects.status_effects.base import EffectType, StatusEffect, StatusEffectFeature
from agent.models.enums import FeatureId


class Dodge(StatusEffect):
    """
    * Attack rolls against the target have disadvantage.
    """

    type: EffectType = EffectType.DODGING
    features: list[StatusEffectFeature] = [
        StatusEffectFeature(ref_id=FeatureId.ATTACKER_DISADVANTAGE),
    ]
