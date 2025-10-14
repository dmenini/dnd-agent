
from __future__ import annotations
from typing import TYPE_CHECKING

from agent.effects.base import StatusEffect
from agent.models.enums import ConditionType

if TYPE_CHECKING:
    from agent.models.character import Character


class Hasted(StatusEffect):
    type: ConditionType = ConditionType.HASTED

    def on_turn_start(self, target: Character):
        """Grant an extra action on each of the target's turns."""
        if target.action_economy.standard_actions > 0:
            target.action_economy.standard_actions += 1

    def on_turn_end(self, target: Character) -> None:
        """Call at the end of the target's turn."""
        self.duration -= 1
