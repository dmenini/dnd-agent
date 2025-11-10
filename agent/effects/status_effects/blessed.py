from agent.effects.status_effects.base import EffectType, StatusEffect, StatusEffectFeature
from agent.models.enums import FeatureId


class Blessed(StatusEffect):
    """
    * +1d4 to target attack rolls
    * +1d4 to target save throws
    """

    type: EffectType = EffectType.BLESSED
    save_dc: int = 0  # Skip save throw as it's cast on a willing creature
    features: list[StatusEffectFeature] = [
        StatusEffectFeature(ref_id=FeatureId.ATTACK_ROLL_BONUS, kwargs={"dice_expr": "1d4"}),
        StatusEffectFeature(ref_id=FeatureId.SAVE_ROLL_BONUS, kwargs={"dice_expr": "1d4"}),
    ]
