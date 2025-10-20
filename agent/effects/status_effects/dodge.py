from typing import Any

from agent.effects.base import EffectType, StatusEffect
from agent.effects.registry import TraitRegistry
from agent.effects.traits import Trait
from agent.jobs.features import FeatureId


class Dodge(StatusEffect):
    """
    * Attack rolls against the target have disadvantage.
    """

    type: EffectType = EffectType.DODGING

    def model_post_init(self, _: Any) -> None:
        self._traits: list[Trait] = [
            TraitRegistry.create(FeatureId.ATTACKER_DISADVANTAGE),
        ]
