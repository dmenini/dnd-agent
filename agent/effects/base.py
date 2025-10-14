from __future__ import annotations

import random
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel

from agent.models.enums import StatType

if TYPE_CHECKING:
    from agent.models.character import Character


class EffectType(str, Enum):
    STUNNED = "stunned"
    PARALYZED = "paralyzed"
    POISONED = "poisoned"
    PRONE = "prone"
    UNCONSCIOUS = "unconscious"
    DODGING = "dodging"
    HASTED = "hasted"
    RESTRAINED = "restrained"


class StatusEffect(BaseModel):
    type: EffectType
    duration: int
    chance: float = 1.0
    save_stat: StatType = StatType.CON
    save_dc: int = 12  # Difficulty class

    def try_apply(self, target: Character) -> bool:
        event = ""
        # Check immunity
        if target.is_immune_to(self.type):
            event += f" {target.name} is immune to {self.type} effect."
            return False

        # Random chance
        if self.chance < 1.0 and random.random() > self.chance:  # noqa: S311
            event += f" The {self.type} effect fails to take hold."
            return False

        # Saving throw
        if self.save_dc:
            roll = target.save_roll(save_stat=self.save_stat)
            if roll.total >= self.save_dc:
                event += (
                    f" {target.name} resists {self.type} with a "
                    f"{self.save_stat.value} save ({roll} vs DC {self.save_dc})!"
                )
                # Negate effect
                return False

        # Apply the effect
        target.apply_status(self)

        # TODO: return event
        return True

    def on_apply(self, target: Character) -> None:
        """Call when the effect is first applied."""

    def on_turn_start(self, target: Character) -> None:
        """Call at the start of the target's turn."""

    def on_turn_end(self, target: Character) -> None:
        """Call at the end of the target's turn."""

    def on_receive_damage(self, target: Character, damage: int) -> int:  # noqa: ARG002
        """Modify damage taken (e.g., resistance, vulnerability)."""
        return damage

    def on_attack_roll(self, *, is_target: bool = False) -> bool | None:  # noqa: ARG002
        """Modify attack roll advantage/disadvantage.
        Return False to signal disadvantage, True for advantage, or None for neutral.
        """
        return None

    def on_save_roll(self, stat: StatType) -> bool | None:  # noqa: ARG002
        """Modify save roll advantage/disadvantage.
        Return False to signal disadvantage, True for advantage, or None for neutral.
        """
        return None

    def on_attack(self, actor: Character, target: Character, damage: int) -> int:  # noqa: ARG002
        """Modify outgoing damage (e.g., weaken attacks)."""
        return damage

    def is_expired(self) -> bool:
        return self.duration <= 0

    def is_auto_crit(self, actor: Character, target: Character) -> bool:  # noqa: ARG002
        return False

    def __str__(self) -> str:
        return f" {{actor}} is {self.type.value} ({self.duration} turns left)."
