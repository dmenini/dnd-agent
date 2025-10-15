from __future__ import annotations

from typing import TYPE_CHECKING

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
    type: EffectType = EffectType.RESTRAINED
    _traits: list[Trait] = [
        CannotMove(),
        DisadvantageOnSavingThrow(),
        AttackerAdvantageOnAttackRoll(),
        TargetDisadvantageOnAttackRoll(),
    ]

    def on_turn_end(self, target: Character) -> None:
        super().on_turn_end(target)
        self.duration -= 1
