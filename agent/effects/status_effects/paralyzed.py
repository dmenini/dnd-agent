from agent.character.abilities import AbilityType
from agent.effects.status_effects.base import EffectType, StatusEffect, StatusEffectFeature
from agent.models.enums import FeatureId

MIN_AUTOCRIT_DISTANCE = 5


class Paralyzed(StatusEffect):
    """
    * Target can't take actions or reactions (incapacitated).
    * Target can't move or speak.
    * Target automatically fails Strength and Dexterity saving throws.
    * Attack rolls against the target have advantage.
    * Any attack that hits the target is a critical hit if the attacker is within 5 feet.
    """

    type: EffectType = EffectType.PARALYZED
    features: list[StatusEffectFeature] = [
        StatusEffectFeature(ref_id=FeatureId.CANNOT_ACT),
        StatusEffectFeature(ref_id=FeatureId.CANNOT_MOVE),
        StatusEffectFeature(ref_id=FeatureId.ATTACKER_ADVANTAGE),
        StatusEffectFeature(ref_id=FeatureId.AUTO_CRIT_IF_MELEE),
        StatusEffectFeature(ref_id=FeatureId.SAVE_FAIL, kwargs={"ability": AbilityType.STR}),
        StatusEffectFeature(ref_id=FeatureId.SAVE_FAIL, kwargs={"ability": AbilityType.DEX}),
    ]
