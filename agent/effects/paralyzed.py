from __future__ import annotations

from typing import TYPE_CHECKING

from agent.effects.base import EffectType, StatusEffect
from agent.effects.traits import AttackerAdvantageOnAttackRoll, AutoCritIfMelee, CannotAct, CannotMove, Trait

if TYPE_CHECKING:
    from agent.character.character import Character

MIN_AUTOCRIT_DISTANCE = 5


class Paralyzed(StatusEffect):
    type: EffectType = EffectType.PARALYZED
    _traits: list[Trait] = [
        CannotAct(),
        CannotMove(),
        AttackerAdvantageOnAttackRoll(),
        AutoCritIfMelee(),
    ]

    def on_turn_end(self, target: Character) -> None:
        super().on_turn_end(target)
        self.duration -= 1
