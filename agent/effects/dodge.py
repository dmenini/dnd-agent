from __future__ import annotations

from typing import TYPE_CHECKING

from agent.effects.base import EffectType, StatusEffect

if TYPE_CHECKING:
    from agent.models.character import Character


class Dodge(StatusEffect):
    type: EffectType = EffectType.DODGING

    def on_turn_start(self, target: Character) -> None:  # noqa: ARG002
        """Grant an extra action on each of the target's turns."""
        self.duration = 0

    def on_attack_roll(self, *, is_target: bool = False) -> bool | None:
        """Attack rolls against the target have disadvantage."""
        return False if is_target else None
