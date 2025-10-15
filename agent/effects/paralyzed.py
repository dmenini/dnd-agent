from __future__ import annotations

from typing import TYPE_CHECKING

from agent.character.stats import StatType
from agent.effects.base import EffectType, StatusEffect
from agent.effects.traits import (
    AttackerAdvantageOnAttackRoll,
    AutoCritIfMelee,
    CannotAct,
    CannotMove,
    FailOnSavingThrow,
    Trait,
)

if TYPE_CHECKING:
    from agent.character.character import Character

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
    _traits: list[Trait] = [
        CannotAct(),
        CannotMove(),
        AttackerAdvantageOnAttackRoll(),
        AutoCritIfMelee(),
        FailOnSavingThrow(stat=StatType.STR),
        FailOnSavingThrow(stat=StatType.DEX),
    ]

    def on_turn_end(self, target: Character) -> None:
        super().on_turn_end(target)
        self.duration -= 1
