from typing import Any

from agent.character.stats import StatType
from agent.effects.base import EffectType, StatusEffect
from agent.effects.registry import TraitRegistry
from agent.effects.traits import Trait
from agent.jobs.feature import FeatureId


class Stunned(StatusEffect):
    """
    * Target can't take actions or reactions (incapacitated).
    * Target can't move.
    * Target can speak only falteringly. -> Not yet implemented
    * Target automatically fails Strength and Dexterity saving throws.
    * Attack rolls against the creature have advantage.
    """

    type: EffectType = EffectType.STUNNED

    def model_post_init(self, _: Any) -> None:
        self._traits: list[Trait] = [
            TraitRegistry.create(FeatureId.CANNOT_ACT),
            TraitRegistry.create(FeatureId.CANNOT_MOVE),
            TraitRegistry.create(FeatureId.ATTACKER_ADVANTAGE),
            TraitRegistry.create(FeatureId.SAVE_FAIL, stat=StatType.STR),
            TraitRegistry.create(FeatureId.SAVE_FAIL, stat=StatType.DEX),
        ]
