from __future__ import annotations

from typing import TYPE_CHECKING

from agent.effects.base import EffectType, StatusEffect
from agent.models.enums import StatType

if TYPE_CHECKING:
    from agent.models.character import Character


class Restrained(StatusEffect):
    type: EffectType = EffectType.RESTRAINED

    def on_apply(self, target: Character) -> None:
        target.action_economy.movement_available = False

    def on_turn_start(self, target: Character) -> None:
        target.action_economy.movement_available = False

    def on_save_roll(self, stat: StatType) -> bool | None:
        """Target has disadvantage on Dexterity saving throws."""
        return False if stat == StatType.DEX else None

    def on_attack_roll(self, *, is_target: bool = True) -> bool | None:
        """Attacks against restrained targets have advantage, and their attack rolls have disadvantage."""
        return is_target

    def on_turn_end(self, target: Character) -> None:  # noqa: ARG002
        """Call at the end of the target's turn."""
        self.duration -= 1
