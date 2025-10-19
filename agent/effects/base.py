from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from pydantic import PrivateAttr

from agent.character.stats import StatType
from agent.effects.traits import Trait
from agent.models.context import CombatContext

if TYPE_CHECKING:
    from agent.character.character import Character


class EffectType(str, Enum):
    STUNNED = "stunned"
    PARALYZED = "paralyzed"
    POISONED = "poisoned"
    DODGING = "dodging"
    HASTED = "hasted"
    RESTRAINED = "restrained"
    LETHARGIC = "lethargic"
    CUSTOM = "custom"


class StatusEffect(Trait):
    type: EffectType
    duration: int
    save_stat: StatType = StatType.CON
    save_dc: int = 12  # Difficulty class

    _traits: list[Trait] = PrivateAttr(default_factory=list)

    @property
    def traits(self) -> list[Trait]:
        return sorted(self._traits, key=lambda t: t.priority)

    def on_apply(self, target: Character) -> None:
        """Call when the effect is first applied."""
        super().on_apply(target)
        for trait in self.traits:
            trait.on_apply(target)

    def on_expire(self, target: Character) -> None:
        """Call when the effect is first applied."""
        super().on_expire(target)
        for trait in self.traits:
            trait.on_expire(target)

    def on_turn_start(self, target: Character) -> None:
        """Call at the start of the target's turn."""
        super().on_turn_start(target)
        for trait in self.traits:
            trait.on_turn_start(target)

    def on_turn_end(self, target: Character) -> None:
        """Call at the end of the target's turn."""
        super().on_turn_end(target)
        for trait in self.traits:
            trait.on_turn_end(target)

    def on_receive_damage(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        """Modify damage taken."""
        super().on_receive_damage(actor, target, ctx)
        for trait in self.traits:
            trait.on_receive_damage(actor, target, ctx)

    def on_apply_damage(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        """Modify outgoing damage."""
        super().on_apply_damage(actor, target, ctx)
        for trait in self.traits:
            trait.on_apply_damage(actor, target, ctx)

    def is_auto_crit(self, actor: Character, target: Character) -> bool:
        """Modify crit chance."""
        for trait in self.traits:
            res = trait.is_auto_crit(actor, target)
            if res is not None:
                return res
        return False

    def is_expired(self) -> bool:
        return self.duration <= 0

    def __str__(self) -> str:
        return f"{self.type.value} ({self.duration} turns left)"
