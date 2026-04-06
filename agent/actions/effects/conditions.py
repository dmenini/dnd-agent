"""Condition effect applicators."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field, field_validator

from agent.actions.effects.base import EffectApplicator
from agent.effects.status_effects.base import StatusEffect, StatusType
from agent.effects.status_effects.registry import StatusEffectRegistry
from agent.logs.log_event import Icon
from agent.services.effect_service import EffectService

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class ApplyConditionsEffect(EffectApplicator):
    """Apply status effects to target.

    Used for:
    - Buff spells (Bless, Haste, Shield of Faith)
    - Debuff spells (Bane, Slow, Hold Person)
    - Weapon effects (poison, stunning strike)
    """

    type: Literal["apply_conditions"] = "apply_conditions"
    conditions: list[StatusEffect] = Field(default_factory=list)
    concentration: bool = Field(
        default=False,
        description="If true, the first condition in the list requires concentration",
        examples=[False, True],
    )

    @field_validator("conditions", mode="before")
    @classmethod
    def resolve_condition_ids(cls, v: list) -> list:
        """Convert string IDs to StatusEffect objects from registry."""
        resolved = []
        for item in v:
            if isinstance(item, str):
                condition = StatusEffectRegistry.get(item)
                if condition is None:
                    msg = f"Unknown status effect: {item}"
                    raise ValueError(msg)
                resolved.append(condition)
            else:
                resolved.append(item)
        return resolved

    def apply(self, actor: Character, target: Character, ctx: CombatContext) -> None:  # noqa: ARG002
        """Apply status effects to target."""
        for condition in self.conditions:
            success = EffectService.try_apply_condition(target, condition)
            if success:
                actor.log_event(f"Applied {condition.type.value} to {target.name}", icon=Icon.EFFECT_APPLIED)


class RemoveConditionsEffect(EffectApplicator):
    """Remove status effects from target.

    Used for:
    - Lesser Restoration (removes paralyzed, poisoned, blinded, deafened)
    - Greater Restoration (removes more conditions)
    - Paladin Lay on Hands (can remove disease/poison)
    """

    type: Literal["remove_conditions"] = "remove_conditions"
    condition_types: list[StatusType] = Field(default_factory=list)

    def apply(self, actor: Character, target: Character, ctx: CombatContext) -> None:  # noqa: ARG002
        """Remove status effects from target."""
        # Try to remove in order (priority matters)
        for cond_type in self.condition_types:
            if EffectService.has_condition(target, cond_type):
                EffectService.remove_condition(target, cond_type)
                actor.log_event(f"Removed {cond_type.value} from {target.name}", icon=Icon.EFFECT_EXPIRED)
                break  # Only remove first match
