from __future__ import annotations

from typing import TYPE_CHECKING

from agent.effects.base import EffectType, StatusEffect
from agent.effects.traits import AttackerAdvantageOnAttackRoll, CannotAct, CannotMove, Trait

if TYPE_CHECKING:
    from agent.character.character import Character


class Stunned(StatusEffect):
    type: EffectType = EffectType.STUNNED
    _traits: list[Trait] = [
        CannotAct(),
        CannotMove(),
        AttackerAdvantageOnAttackRoll(),
    ]

    def on_turn_end(self, target: Character) -> None:
        super().on_turn_end(target)
        self.duration -= 1
