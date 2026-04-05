"""Composable action system."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from pydantic import Discriminator, Field

from agent.actions.base import Action, ActionCategory
from agent.actions.conditions.armor_restriction import ArmorRestrictionCondition
from agent.actions.conditions.requires_prior_action import RequiresPriorActionCondition
from agent.actions.conditions.resource_threshold import ResourceThresholdCondition
from agent.actions.effects.conditions import ApplyConditionsEffect, RemoveConditionsEffect
from agent.actions.effects.damage import DamageEffect
from agent.actions.effects.distributed import DistributedHealingEffect
from agent.actions.effects.dynamic_status import ApplyDynamicStatusEffect
from agent.actions.effects.evocation import SummonEvocationEffect
from agent.actions.effects.healing import HealingEffect
from agent.actions.effects.resources import RecoverSpellSlotsEffect, RestoreResourceEffect
from agent.actions.resources.action_economy import ActionEconomyConsumer
from agent.actions.resources.limited_uses import LimitedUsesConsumer
from agent.actions.resources.spell_slots import SpellSlotConsumer
from agent.actions.strategies.attack_roll import AttackRollStrategy
from agent.actions.strategies.auto_success import AutoSuccessStrategy
from agent.actions.strategies.saving_throw import SavingThrowStrategy
from agent.models.enums import EventType
from agent.services.effect_service import EffectService
from agent.services.trait_service import TraitService

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.character.resources import ActionEconomy
    from agent.models.context import CombatContext


class ComposableAction(Action):
    """Data-driven action using composable primitives.

    Every action is composed of:
    1. Availability conditions (when the action can be used)
    2. Resolution strategy (how to determine success/failure)
    3. Effect applicators (what happens on success)
    4. Resource consumers (what it costs)

    This allows defining abilities as JSON data instead of Python classes.
    """

    # Composable components
    conditions: list[
        Annotated[
            RequiresPriorActionCondition | ArmorRestrictionCondition | ResourceThresholdCondition,
            Discriminator("type"),
        ]
    ] = Field(default_factory=list)
    resolution: Annotated[AutoSuccessStrategy | AttackRollStrategy | SavingThrowStrategy, Discriminator("type")]
    effects: list[
        Annotated[
            DamageEffect
            | HealingEffect
            | ApplyConditionsEffect
            | RemoveConditionsEffect
            | SummonEvocationEffect
            | RecoverSpellSlotsEffect
            | RestoreResourceEffect
            | ApplyDynamicStatusEffect
            | DistributedHealingEffect,
            Discriminator("type"),
        ]
    ] = Field(default_factory=list)
    resources: list[
        Annotated[ActionEconomyConsumer | SpellSlotConsumer | LimitedUsesConsumer, Discriminator("type")]
    ] = Field(default_factory=list)
    level: int | None = 1

    def execute(self, actor: Character, target: Any, ctx: CombatContext) -> None:
        """Execute the action using composable primitives.

        Args:
            actor: Character performing the action
            target: Target of the action (Character for most actions, Position for evocations)
            ctx: Combat context
        """
        # Fire start events (only for Character targets)
        from agent.models.position import Position  # noqa: PLC0415

        if not isinstance(target, Position):
            TraitService.trigger_event(actor, EventType.COMBAT_START, actor, target, ctx)
            TraitService.trigger_event(target, EventType.COMBAT_START, actor, target, ctx)

        # Handle concentration before resolving
        requires_concentration = self.metadata.get("concentration", False)
        if requires_concentration:
            self._handle_concentration(actor)

        # Resolve (determine success/failure)
        # For position-based targeting (evocations), skip resolution and auto-succeed
        success = True if isinstance(target, Position) else self.resolution.resolve(actor, target, ctx)

        # Apply effects (if successful, or if apply_on_failure is True)
        if success or self.resolution.apply_on_failure:
            for effect in self.effects:
                effect.apply(actor, target, ctx)

        # Fire end events (only for Character targets)
        if not isinstance(target, Position):
            TraitService.trigger_event(actor, EventType.COMBAT_END, actor, target, ctx)
            TraitService.trigger_event(target, EventType.COMBAT_END, actor, target, ctx)

    def _handle_concentration(self, actor: Character) -> None:
        """Break existing concentration and set up new concentration."""
        # Break existing concentration
        if actor.concentrating_on:
            old_effect = actor.concentrating_on
            EffectService.remove_condition(actor, old_effect.type)
            actor.log_event(f"{actor.name} stops concentrating on {old_effect.type.value}")

        # Track new concentration - find the first status effect being applied
        for effect in self.effects:
            if isinstance(effect, ApplyConditionsEffect) and effect.conditions:
                actor.concentrating_on = effect.conditions[0]
                break

    def finalize(self, actor: Character) -> None:
        """Consume resources after action execution."""
        for consumer in self.resources:
            consumer.consume(actor)

    def is_available(self, action_economy: ActionEconomy, actor: Character | None = None) -> bool:
        """Check if action is available (has resources and action economy).

        Args:
            action_economy: Action economy to check
            actor: Optional actor for condition checking (required for conditions)

        Returns:
            True if action can be used
        """
        # Check availability conditions first
        if actor:
            for condition in self.conditions:
                if not condition.is_available(actor):
                    return False

        # Check action economy
        for consumer in self.resources:
            if hasattr(consumer, "is_available"):
                # Note: We need the actor, not just action_economy
                # This is a limitation - we'll need to refactor this slightly
                # For now, just check action economy consumers
                from agent.actions.resources.action_economy import ActionEconomyConsumer  # noqa: PLC0415

                if isinstance(consumer, ActionEconomyConsumer):
                    if self.category == ActionCategory.STANDARD:
                        return action_economy.can_use_standard(self.type)
                    if self.category == ActionCategory.BONUS:
                        return action_economy.can_use_bonus(self.type)
                    if self.category == ActionCategory.REACTION:
                        return action_economy.can_use_reaction()

        return True

    def __str__(self) -> str:
        """Return concise string for NPC AI prompts."""
        return (
            f"- {self.id}: {self.name} — {self.description} "
            f"(Type: {self.type.value}, Category: {self.category.value}, "
            f"Targeting: {self.targeting.value}, Hits: {self.hits}, Range: {self.range} m)"
        )


# Type union for discriminated union serialization
ActionDefinition = Annotated[ComposableAction, Field(discriminator="category")]
