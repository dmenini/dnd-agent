from typing import Literal

from agent.character.stats import StatType
from agent.effects.status_effects.base import EffectType, StatusEffect, StatusEffectFeature
from agent.models.enums import FeatureId


class Lethargic(StatusEffect):
    """
    * Target's movement speed is halved.
    * Target may only take half actions per turn (rounded up).
    Target may repeat the WIS saving throw with disadvantage each turn, ending the effect on a success.
    """

    type: EffectType = EffectType.LETHARGIC
    save_stat: StatType = StatType.WIS
    save_mode: Literal["start"] = "start"
    features: list[StatusEffectFeature] = [
        StatusEffectFeature(ref_id=FeatureId.SPEED_MULTIPLIER, kwargs={"value": 0.5}),
        StatusEffectFeature(ref_id=FeatureId.SAVE_DISADVANTAGE, kwargs={"stat": StatType.WIS}),
        StatusEffectFeature(ref_id=FeatureId.HALF_ATTACKS, kwargs={}),
    ]
