from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agent.effects.base import EffectType, StatusEffect
from agent.effects.traits import DamageOverTime, TargetDisadvantageOnAttackRoll
from agent.equipment.weapons import DamageType

if TYPE_CHECKING:
    from agent.character.character import Character


class Poisoned(StatusEffect):
    """
    * Target has disadvantage on attack rolls and ability checks.
    * Target takes damage over time.
    """

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
