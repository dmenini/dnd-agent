from __future__ import annotations

from typing import TYPE_CHECKING

from agent.character.stats import StatType
from agent.effects.base import EffectType, StatusEffect
from agent.effects.traits import (
    AttackerAdvantageOnAttackRoll,
    CannotMove,
    DisadvantageOnSavingThrow,
    TargetDisadvantageOnAttackRoll,
    Trait,
)

if TYPE_CHECKING:
    from agent.character.character import Character


class Restrained(StatusEffect):
    """
    * Target's speed becomes 0 -> Modeled as no movement.
    * Target can't benefit from any bonus to its speed -> Modeled as no movement.
    * Attack rolls against the target have advantage.
    * Target attack rolls have disadvantage.
    * Target has disadvantage on Dexterity saving throws.
    """

    type: EffectType = EffectType.RESTRAINED
    _traits: list[Trait] = [
        CannotMove(),
        DisadvantageOnSavingThrow(stat=StatType.DEX),
        AttackerAdvantageOnAttackRoll(),
        TargetDisadvantageOnAttackRoll(),
    ]

    def on_turn_end(self, target: Character) -> None:
        super().on_turn_end(target)
        self.duration -= 1
