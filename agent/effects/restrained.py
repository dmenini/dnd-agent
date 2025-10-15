from __future__ import annotations

from typing import TYPE_CHECKING

from agent.effects.base import EffectType, StatusEffect
from agent.effects.traits import (
    AttackerAdvantageOnAttackRoll,
    CannotMove,
    DisadvantageOnDexSavingThrow,
    TargetDisadvantageOnAttackRoll,
    Trait,
)

if TYPE_CHECKING:
    from agent.models.character import Character


class Restrained(StatusEffect):
    type: EffectType = EffectType.RESTRAINED
    _traits: list[Trait] = [
        CannotMove(),
        DisadvantageOnDexSavingThrow(),
        AttackerAdvantageOnAttackRoll(),
        TargetDisadvantageOnAttackRoll(),
    ]

    def on_turn_end(self, target: Character) -> None:
        super().on_turn_end(target)
        self.duration -= 1
