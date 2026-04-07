"""Registry for pre-built status effects."""

from agent.effects.status_effects.base import StatusEffect
from agent.effects.status_effects.collection import (
    Blessed,
    DivineFavored,
    Enraged,
    Hasted,
    MagicWeapon,
    ShieldedByFaith,
)


class StatusEffectRegistry:
    """Global registry for pre-built status effects."""

    _effects: dict[str, StatusEffect] = {
        "blessed": Blessed,
        "divine_favored": DivineFavored,
        "enraged": Enraged,
        "hasted": Hasted,
        "magic_weapon": MagicWeapon,
        "shielded_by_faith": ShieldedByFaith,
    }

    @classmethod
    def get(cls, name: str) -> StatusEffect:
        """Get status effect by name."""
        effect = cls._effects.get(name.lower())
        if not effect:
            msg = f"Status effect '{name}' not found in registry"
            raise KeyError(msg)
        # Return a deep copy to avoid shared state issues
        return effect.model_copy(deep=True)

    @classmethod
    def register(cls, name: str, effect: StatusEffect) -> None:
        """Register a status effect."""
        cls._effects[name.lower()] = effect

    @classmethod
    def list_all(cls) -> list[str]:
        """List all registered status effect names."""
        return list(cls._effects.keys())
