from __future__ import annotations

from typing import TYPE_CHECKING

from agent.effects.base import EffectType, StatusEffect

if TYPE_CHECKING:
    from agent.models.character import Character


class Poisoned(StatusEffect):
    type: EffectType = EffectType.POISONED
    damage: int = 1

    def on_turn_end(self, target: Character) -> None:
        """Target takes poison damage at the end of its turn."""
        target.apply_damage(self.damage)
        self.duration -= 1
