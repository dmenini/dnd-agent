from __future__ import annotations

from typing import TYPE_CHECKING

from agent.effects.base import EffectType, StatusEffect

if TYPE_CHECKING:
    from agent.models.character import Character

MIN_AUTOCRIT_DISTANCE = 5


class Paralyzed(StatusEffect):
    type: EffectType = EffectType.PARALYZED

    def on_turn_start(self, target: Character) -> None:
        """Target cannot act or move."""
        target.action_economy.standard_actions = -1  # Cannot act
        target.action_economy.bonus_actions = -1  # Cannot act
        target.action_economy.movement_available = False  # Cannot move

    def on_attack_roll(self, *, is_target: bool = False) -> bool | None:
        """Attack rolls against the target have advantage."""
        return True if is_target else None

    def is_auto_crit(self, actor: Character, target: Character) -> bool:
        """Critical hits on melee attacks within 5ft applied in action itself."""
        return actor.distance(target.pos) <= MIN_AUTOCRIT_DISTANCE

    def on_turn_end(self, target: Character) -> None:  # noqa: ARG002
        """Call at the end of the target's turn."""
        self.duration -= 1
