"""Resource manipulation effect applicators."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from agent.actions.effects.base import EffectApplicator
from agent.actions.expressions import ExpressionEvaluator
from agent.logs.log_event import LogLevel

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class RecoverSpellSlotsEffect(EffectApplicator):
    """Recover expended spell slots up to a limit.

    Used for:
    - Arcane Recovery (Wizard): recover slots up to half wizard level
    - Sorcerer Font of Magic: convert sorcery points to spell slots
    - Other spell slot recovery features
    """

    type: Literal["recover_spell_slots"] = Field(
        default="recover_spell_slots",
        description="Effect type identifier",
    )
    max_level: str | int = Field(
        default="{level} / 2",
        description="Expression for max slot levels to recover",
        examples=["{level} / 2", 5],
    )
    round_up: bool = Field(
        default=True,
        description="If true, round up fractional max_level values",
    )
    strategy: Literal["highest_first", "lowest_first"] = Field(
        default="highest_first",
        description="Which spell slots to recover first",
    )

    def apply(self, actor: Character, target: Character, ctx: CombatContext) -> None:  # noqa: ARG002
        """Recover spell slots for the actor."""
        # Evaluate max recovery amount
        max_recovery = ExpressionEvaluator.eval(self.max_level, actor)
        if self.round_up and isinstance(max_recovery, float):
            max_recovery = int(max_recovery) + (1 if max_recovery % 1 > 0 else 0)
        max_recovery = int(max_recovery)

        recovered = 0
        slots_recovered_by_level = {}

        # Sort slot levels based on strategy
        slot_levels = sorted(
            actor.spell_slots.slots.keys(),
            key=lambda x: x.value,
            reverse=(self.strategy == "highest_first"),
        )

        # Iterate through spell slot levels
        for level in slot_levels:
            current = actor.spell_slots.slots[level]
            maximum = actor.spell_slots.max_slots[level]

            if current < maximum:
                # Calculate how many slots we can recover at this level
                # We can't exceed max_recovery in total slot levels
                slots_available = maximum - current
                levels_needed_per_slot = level.value
                slots_to_recover = min(
                    slots_available,
                    (max_recovery - recovered) // levels_needed_per_slot if levels_needed_per_slot > 0 else 0,
                )

                if slots_to_recover <= 0:
                    continue

                # Recover the slots
                actor.spell_slots.slots[level] += slots_to_recover
                recovered += slots_to_recover * levels_needed_per_slot
                slots_recovered_by_level[level] = slots_to_recover

                if recovered >= max_recovery:
                    break

        # Log recovery
        if slots_recovered_by_level:
            recovery_desc = ", ".join(
                [f"{count}x level {level.value}" for level, count in slots_recovered_by_level.items()]
            )
            actor.log_event(
                f"{actor.name} focuses their mind and recovers spell slots: {recovery_desc}",
                log_type=LogLevel.DETAIL,
            )
        else:
            actor.log_event(
                f"{actor.name} has no spell slots to recover.",
                log_type=LogLevel.DETAIL,
            )


class RestoreResourceEffect(EffectApplicator):
    """Restore a limited resource.

    Used for:
    - Restore specific resource by amount
    - Heal HP
    - Restore Ki points, Sorcery points, etc.
    """

    type: Literal["restore_resource"] = Field(default="restore_resource", description="Effect type identifier")
    resource_name: str = Field(description="Name of the resource to restore (e.g., 'Ki', 'Rage', 'Channel Divinity')")
    amount: str | int = Field(
        default="{max}", description="Amount to restore, or '{max}' to restore all (e.g., '1', '2', '{max}')"
    )

    def apply(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        """Restore resource for the target."""
        resource = target.limited_resources.get(self.resource_name)
        if resource is None:
            target.log_event(
                f"Resource '{self.resource_name}' not found on {target.name}",
                log_type=LogLevel.DETAIL,
            )
            return

        # Evaluate amount
        if self.amount == "{max}":
            restore_amount = resource.max_uses - resource.current_uses
        else:
            restore_amount = int(ExpressionEvaluator.eval(self.amount, actor, target, ctx))

        # Apply restoration
        old_uses = resource.current_uses
        resource.current_uses = max(0, resource.current_uses - restore_amount)
        actual_restored = old_uses - resource.current_uses

        if actual_restored > 0:
            target.log_event(
                f"{target.name} restores {actual_restored} uses of {self.resource_name}",
                log_type=LogLevel.DETAIL,
            )
