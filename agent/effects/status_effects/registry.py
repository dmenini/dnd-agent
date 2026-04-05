"""Registry for pre-built status effects."""

from agent.effects.status_effects.base import StatusEffect, StatusType
from agent.effects.status_effects.collection import (
    Blessed,
    DivineFavored,
    MagicWeapon,
    ShieldedByFaith,
)


class StatusEffectRegistry:
    """Global registry for pre-built status effects."""

    _effects: dict[str, StatusEffect] = {
        "blessed": Blessed,
        "divine_favored": DivineFavored,
        "magic_weapon": MagicWeapon,
        "shielded_by_faith": ShieldedByFaith,
    }

    @classmethod
    def get(cls, name: str) -> StatusEffect:
        """Get status effect by name."""
        effect = cls._effects.get(name.lower())
        if not effect:
            raise KeyError(f"Status effect '{name}' not found in registry")
        # Return a copy with default duration
        return effect.model_copy()

    @classmethod
    def register(cls, name: str, effect: StatusEffect) -> None:
        """Register a status effect."""
        cls._effects[name.lower()] = effect

    @classmethod
    def list_all(cls) -> list[str]:
        """List all registered status effect names."""
        return list(cls._effects.keys())
