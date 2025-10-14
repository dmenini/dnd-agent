from __future__ import annotations

from typing import TYPE_CHECKING

from agent.effects.base import EffectType, StatusEffect

if TYPE_CHECKING:
    from agent.models.character import Character


class Hasted(StatusEffect):
    type: EffectType = EffectType.HASTED

    def on_turn_start(self, target: Character) -> None:
        """Grant an extra action on each of the target's turns."""
        if target.action_economy.standard_actions > 0:
            target.action_economy.standard_actions += 1

    def on_turn_end(self, target: Character) -> None:  # noqa: ARG002
        """Call at the end of the target's turn."""
        self.duration -= 1
