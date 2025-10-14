from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

from agent.models.enums import ConditionType

if TYPE_CHECKING:
    from agent.models.character import Character


class StatusEffect(BaseModel):
    type: ConditionType
    duration: int

    def on_apply(self, target: Character) -> None:
        """Call when the effect is first applied."""
        pass

    def on_turn_start(self, target: Character) -> None:
        """Call at the start of the target's turn."""
        pass

    def on_turn_end(self, target: Character) -> None:
        """Call at the end of the target's turn."""
        pass

    def on_receive_damage(self, target: Character, damage: int) -> int:
        """Modify damage taken (e.g., resistance, vulnerability)."""
        return damage

    def on_attack_roll(self, actor: Character, target: Character) -> bool | None:
        """Modify attack toll advantage/disadvantage.
        Return False to signal disadvantage, True for advantage, or None for neutral.
        """
        return None

    def on_attack(self, actor: Character, target: Character, damage: int) -> int:
        """Modify outgoing damage (e.g., weaken attacks)."""
        return damage

    def is_expired(self) -> bool:
        return self.duration <= 0

    def __str__(self) -> str:
        return f" {{actor}} is {self.type.value} ({self.duration} turns left)."
