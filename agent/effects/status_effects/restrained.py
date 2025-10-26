from agent.character.stats import StatType
from agent.effects.status_effects.base import EffectType, StatusEffect, StatusEffectFeature
from agent.models.enums import FeatureId


class Restrained(StatusEffect):
    """
    * Target's speed becomes 0 -> Modeled as no movement.
    * Target can't benefit from any bonus to its speed -> Modeled as no movement.
    * Attack rolls against the target have advantage.
    * Target attack rolls have disadvantage.
    * Target has disadvantage on Dexterity saving throws.
    """

    type: EffectType = EffectType.RESTRAINED
    features: list[StatusEffectFeature] = [
        StatusEffectFeature(ref_id=FeatureId.CANNOT_MOVE),
        StatusEffectFeature(ref_id=FeatureId.SAVE_DISADVANTAGE, kwargs={"stat": StatType.DEX}),
        StatusEffectFeature(ref_id=FeatureId.ATTACKER_ADVANTAGE),
        StatusEffectFeature(ref_id=FeatureId.TARGET_DISADVANTAGE),
    ]
