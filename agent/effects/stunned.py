from __future__ import annotations
from typing import TYPE_CHECKING

from agent.effects.base import StatusEffect
from agent.models.enums import ConditionType

if TYPE_CHECKING:
    from agent.models.character import Character


class Stunned(StatusEffect):
    type: ConditionType = ConditionType.STUNNED

    def on_turn_start(self, target: Character) -> None:
        """Target cannot act or move."""
        target.can_act = False

    def on_attack_roll(self, actor: Character, target: Character) -> bool | None:
        """Attacks against stunned targets have advantage."""
        return True

    def on_turn_end(self, target: Character) -> None:
        """Call at the end of the target's turn."""
        self.duration -= 1
