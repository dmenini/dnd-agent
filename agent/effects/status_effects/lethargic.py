from typing import Any, Literal

from agent.character.stats import StatType
from agent.effects.base import EffectType, StatusEffect
from agent.effects.registry import TraitRegistry
from agent.effects.traits import (
    Trait,
)
from agent.jobs.feature import FeatureId


class Lethargic(StatusEffect):
    """
    * Target's movement speed is halved.
    * Target may only take half actions per turn (rounded up).
    Target may repeat the WIS saving throw with disadvantage each turn, ending the effect on a success.
    """

    type: EffectType = EffectType.LETHARGIC
    save_stat: StatType = StatType.WIS
    save_mode: Literal["start"] = "start"

    def model_post_init(self, _: Any) -> None:
        self._traits: list[Trait] = [
            TraitRegistry.create(FeatureId.SPEED_MULTIPLIER, value=0.5),
            TraitRegistry.create(FeatureId.SAVE_DISADVANTAGE, stat=StatType.WIS),
            TraitRegistry.create(FeatureId.HALF_ATTACKS),
        ]
