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

    def on_attack_roll(self, actor: Character, target: Character) -> bool | None:  # noqa: ARG002
        """When the actor rolls against this target, the attack is at disadvantage."""
        return False  # Always imposes disadvantage on attackers
