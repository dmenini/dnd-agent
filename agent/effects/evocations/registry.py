"""Registry for evocation templates."""

from __future__ import annotations

from agent.actions.base import ActionCategory
from agent.character.abilities import AbilityType
from agent.effects.evocations.base import Evocation
from agent.jobs.feature import JobFeature
from agent.models.constants import MELEE_RANGE
from agent.models.damage import DamageType
from agent.models.enums import FeatureId, TargetingType


class EvocationRegistry:
    """Registry for looking up evocation templates by ID.

    Evocations are complex objects that contain features and action economy.
    Rather than serializing them fully in JSON, we define them here and
    reference them by ID from composable action definitions.
    """

    _evocations: dict[str, Evocation] = {}

    @classmethod
    def register(cls, evocation_id: str, evocation: Evocation) -> None:
        """Register an evocation template."""
        cls._evocations[evocation_id] = evocation

    @classmethod
    def get(cls, evocation_id: str) -> Evocation | None:
        """Get evocation template by ID.

        Returns a copy of the template to avoid mutation issues.
        """
        template = cls._evocations.get(evocation_id)
        if template is None:
            return None
        # Return a copy to avoid shared state issues
        return template.model_copy(deep=True)

    @classmethod
    def list_all(cls) -> list[str]:
        """List all registered evocation IDs."""
        return list(cls._evocations.keys())


# Register built-in evocations
def _register_spiritual_weapon() -> None:
    """Register Spiritual Weapon evocation for War Domain clerics."""
    attack = JobFeature(
        ref_id=FeatureId.MELEE_SPELL_ATTACK,
        name="Spiritual Weapon Attack",
        description="The spiritual weapon attacks a creature within 5 feet.",
        kwargs={
            "range": MELEE_RANGE,
            "damage_dice": "1d8",
            "damage_type": DamageType.FORCE,
            "weapon_type": "magic",
            "targeting": TargetingType.SINGLE,
            "ability": AbilityType.WIS,
            "casting_time": ActionCategory.BONUS,
            "breaks_stealth": False,
        },
    )
    move = JobFeature(
        ref_id=FeatureId.REPOSITION_EVOCATION,
        name="Move Spiritual Weapon",
        description="Move the weapon up to 20 feet.",
        kwargs={
            "range": 20,
            "evocation_name": "Spiritual Weapon",
            "casting_time": ActionCategory.MOVEMENT,
            "breaks_stealth": False,
        },
    )
    evocation = Evocation(
        source_id=FeatureId.SPIRITUAL_WEAPON.value,
        name="Spiritual Weapon",
        duration=10,  # 1 minute = 10 rounds
        features=[attack, move],
        on_cast_use=attack.ref_id,
    )
    EvocationRegistry.register("spiritual_weapon", evocation)


# Initialize registry
_register_spiritual_weapon()
