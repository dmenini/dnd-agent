from typing import Any

from agent.character.abilities import AbilityType
from agent.effects.status_effects.base import EffectType, StatusEffect, StatusEffectFeature
from agent.models.damage import DamageType
from agent.models.enums import FeatureId


class Enraged(StatusEffect):
    """
    * You have advantage on Strength checks and Strength saving throws.
    * When you make a melee weapon attack using Strength, you gain a bonus to the damage roll.
    * You have resistance to bludgeoning, piercing, and slashing damage.
    * If you are able to cast spells, you can't cast them or concentrate on them while raging.
    """

    type: EffectType = EffectType.ENRAGED
    features: list[StatusEffectFeature] = [
        StatusEffectFeature(ref_id=FeatureId.SAVE_ADVANTAGE, kwargs={"ability": AbilityType.STR}),
        StatusEffectFeature(ref_id=FeatureId.RESISTANCE, kwargs={"damage_type": DamageType.BLUDGEONING}),
        StatusEffectFeature(ref_id=FeatureId.RESISTANCE, kwargs={"damage_type": DamageType.PIERCING}),
        StatusEffectFeature(ref_id=FeatureId.RESISTANCE, kwargs={"damage_type": DamageType.SLASHING}),
    ]
    duration: int = 1
    damage_bonus: int = 2

    def model_post_init(self, _: Any, /) -> None:
        feat = StatusEffectFeature(ref_id=FeatureId.DAMAGE_BONUS_WITH_MELEE_WEAPON, kwargs={"value": self.damage_bonus})
        self.features.append(feat)
