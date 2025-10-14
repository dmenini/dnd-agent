from __future__ import annotations

from typing import TYPE_CHECKING

from agent.effects.base import EffectType, StatusEffect

if TYPE_CHECKING:
    from agent.models.character import Character


class Stunned(StatusEffect):
    type: EffectType = EffectType.STUNNED

    def on_turn_start(self, target: Character) -> None:
        """Target cannot act or move."""
        target.action_economy.standard_actions = -1
        target.action_economy.bonus_actions = -1
        target.action_economy.reaction_available = False
        target.action_economy.movement_available = False

    def on_attack_roll(self, *, is_target: bool = True) -> bool | None:
        """Attacks against stunned targets have advantage."""
        return True if is_target else None

    def on_turn_end(self, target: Character) -> None:  # noqa: ARG002
        """Call at the end of the target's turn."""
        self.duration -= 1
