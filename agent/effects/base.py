from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, PrivateAttr

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


class StatusEffect(BaseModel):
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
        for trait in self.traits:
            self._trigger_hook(trait, "on_apply", target)

    def on_expire(self, target: Character) -> None:
        """Call when the effect is first applied."""
        for trait in self.traits:
            self._trigger_hook(trait, "on_expire", target)

    def on_turn_start(self, target: Character) -> None:
        """Call at the start of the target's turn."""
        for trait in self.traits:
            self._trigger_hook(trait, "on_turn_start", target)

    def on_turn_end(self, target: Character) -> None:
        """Call at the end of the target's turn."""
        for trait in self.traits:
            self._trigger_hook(trait, "on_turn_end", target)

    def on_receive_damage(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        """Modify damage taken."""
        if ctx.damage is None:
            return
        for trait in self.traits:
            self._trigger_hook(trait, "on_receive_damage", actor, target, ctx)

    def on_apply_damage(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        """Modify outgoing damage."""
        if ctx.damage is None:
            return
        for trait in self.traits:
            self._trigger_hook(trait, "on_apply_damage", actor, target, ctx)

    def is_auto_crit(self, actor: Character, target: Character) -> bool:
        """Modify crit chance."""
        for trait in self.traits:
            res = self._trigger_hook(trait, "is_auto_crit", actor, target)
            if res is not None:
                return res
        return False

    def is_expired(self) -> bool:
        return self.duration <= 0

    def _trigger_hook(self, trait: Trait, hook_name: str, *args: Any, **kwargs: Any) -> Any:
        """Call all traits that define the given hook."""
        method = getattr(trait, hook_name, None)
        return method(*args, **kwargs) if method is not None else None

    def __str__(self) -> str:
        return f"{self.type.value} ({self.duration} turns left)"
