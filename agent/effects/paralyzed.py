from __future__ import annotations
from typing import TYPE_CHECKING

from agent.effects.base import StatusEffect
from agent.models.enums import ConditionType

if TYPE_CHECKING:
    from agent.models.character import Character


class Paralyzed(StatusEffect):
    type: ConditionType = ConditionType.PARALYZED

    def on_turn_start(self, target: Character):
        """Target cannot act or move."""
        target.action_economy.standard_actions = -1  # Cannot act
        target.action_economy.bonus_actions = -1  # Cannot act
        target.action_economy.movement_available = False  # Cannot move

    def on_attack_roll(
        self, actor: Character, target: Character
    ) -> bool | None:
        """
        Attack rolls against the target have advantage.
        Critical hits on melee attacks within 5ft applied in action itself.
        """
        return True

    def on_turn_end(self, target: Character) -> None:
        """Call at the end of the target's turn."""
        self.duration -= 1
