from __future__ import annotations

from typing import TYPE_CHECKING

from agent.effects.base import EffectType, StatusEffect
from agent.effects.traits import AttackerDisadvantageOnAttackRoll, Trait

if TYPE_CHECKING:
    from agent.character.character import Character


class Dodge(StatusEffect):
    type: EffectType = EffectType.DODGING
    _traits: list[Trait] = [AttackerDisadvantageOnAttackRoll()]

    def on_turn_start(self, target: Character) -> None:
        super().on_turn_start(target)
        self.duration = 0
