from typing import Any

from agent.character.stats import StatType
from agent.effects.base import EffectType, StatusEffect
from agent.effects.registry import TraitRegistry
from agent.effects.traits import Trait
from agent.jobs.feature import FeatureId

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

    def model_post_init(self, _: Any) -> None:
        self._traits: list[Trait] = [
            TraitRegistry.create(FeatureId.CANNOT_ACT),
            TraitRegistry.create(FeatureId.CANNOT_MOVE),
            TraitRegistry.create(FeatureId.ATTACKER_ADVANTAGE),
            TraitRegistry.create(FeatureId.AUTO_CRIT_IF_MELEE),
            TraitRegistry.create(FeatureId.SAVE_FAIL, stat=StatType.STR),
            TraitRegistry.create(FeatureId.SAVE_FAIL, stat=StatType.DEX),
        ]
