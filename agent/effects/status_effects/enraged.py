from agent.character.stats import StatType
from agent.effects.status_effects.base import EffectType, StatusEffect, StatusEffectFeature
from agent.models.enums import FeatureId


class Enraged(StatusEffect):
    """
    * Advantage on STR checks
    * +2 bonus damage
    """

    type: EffectType = EffectType.ENRAGED
    features: list[StatusEffectFeature] = [
        StatusEffectFeature(ref_id=FeatureId.SAVE_ADVANTAGE, kwargs={"stat": StatType.STR}),
        StatusEffectFeature(ref_id=FeatureId.DAMAGE_BONUS, kwargs={"value": 2}),  # TODO: Only melee damage
    ]
    duration: int = 1
