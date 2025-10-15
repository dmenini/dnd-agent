from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agent.effects.base import EffectType, StatusEffect
from agent.effects.traits import DamageOverTime, TargetDisadvantageOnAttackRoll
from agent.models.enums import DamageType

if TYPE_CHECKING:
    from agent.character.character import Character


class Poisoned(StatusEffect):
    type: EffectType = EffectType.POISONED
    damage: int = 1

    def model_post_init(self, _: Any) -> None:
        self._traits = [
            TargetDisadvantageOnAttackRoll(),
            DamageOverTime(damage=self.damage, dtype=DamageType.POISON),
        ]

    def on_turn_end(self, target: Character) -> None:
        super().on_turn_end(target)
        self.duration -= 1
