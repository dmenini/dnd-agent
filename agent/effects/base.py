from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, PrivateAttr

from agent.character.stats import StatType
from agent.effects.traits import Trait

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


class StatusEffect(BaseModel):
    type: EffectType
    duration: int
    save_stat: StatType = StatType.CON
    save_dc: int = 12  # Difficulty class

    _traits: list[Trait] = PrivateAttr(default_factory=list)

    def on_apply(self, target: Character) -> None:
        """Call when the effect is first applied."""
        for trait in self._traits:
            self._trigger_hook(trait, "on_apply", target)

    def on_expire(self, target: Character) -> None:
        """Call when the effect is first applied."""
        for trait in self._traits:
            self._trigger_hook(trait, "on_expire", target)

    def on_turn_start(self, target: Character) -> None:
        """Call at the start of the target's turn."""
        for trait in self._traits:
            self._trigger_hook(trait, "on_turn_start", target)

    def on_turn_end(self, target: Character) -> None:
        """Call at the end of the target's turn."""
        for trait in self._traits:
            self._trigger_hook(trait, "on_turn_end", target)

    def on_receive_damage(self, target: Character, damage: int) -> int:
        """Modify damage taken (e.g., resistance, vulnerability). Multiple effects accumulate on each other."""
        for trait in self._traits:
            damage += self._trigger_hook(trait, "on_receive_damage", target, damage) or 0
        return damage

    def on_attack(self, actor: Character, target: Character, damage: int) -> int:
        """Modify outgoing damage (e.g., weaken attacks)."""
        for trait in self._traits:
            damage += self._trigger_hook(trait, "on_attack", actor, target, damage) or 0
        return damage

    def is_auto_crit(self, actor: Character, target: Character) -> bool:
        """Modify crit chance."""
        for trait in self._traits:
            return self._trigger_hook(trait, "is_auto_crit", actor, target)
        return False

    def is_expired(self) -> bool:
        return self.duration <= 0

    def __str__(self) -> str:
        return f" {{actor}} is {self.type.value} ({self.duration} turns left)."

    def _trigger_hook(self, trait: Trait, hook_name: str, *args: Any, **kwargs: Any) -> Any:
        """Call all traits that define the given hook."""
        method = getattr(trait, hook_name, None)
        return method(*args, **kwargs) if method is not None else None
