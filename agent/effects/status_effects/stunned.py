from agent.character.stats import StatType
from agent.effects.status_effects.base import EffectType, StatusEffect, StatusEffectFeature
from agent.models.enums import FeatureId


class Stunned(StatusEffect):
    """
    * Target can't take actions or reactions (incapacitated).
    * Target can't move.
    * Target can speak only falteringly. -> Not yet implemented
    * Target automatically fails Strength and Dexterity saving throws.
    * Attack rolls against the creature have advantage.
    """

    type: EffectType = EffectType.STUNNED
    features: list[StatusEffectFeature] = [
        StatusEffectFeature(ref_id=FeatureId.CANNOT_ACT),
        StatusEffectFeature(ref_id=FeatureId.CANNOT_MOVE),
        StatusEffectFeature(ref_id=FeatureId.ATTACKER_ADVANTAGE),
        StatusEffectFeature(ref_id=FeatureId.SAVE_FAIL, kwargs={"stat": StatType.STR}),
        StatusEffectFeature(ref_id=FeatureId.SAVE_FAIL, kwargs={"stat": StatType.DEX}),
    ]
