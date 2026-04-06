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
from agent.models.position import Position
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

    Examples:
        Simple melee attack:
        {
            "id": "longsword_attack",
            "name": "Longsword Attack",
            "description": "Strike with your longsword",
            "type": "attack",
            "category": "standard",
            "targeting": "single",
            "range": 1.5,
            "hits": 1,
            "resolution": {"type": "attack_roll", "ability": "strength", "weapon_type": "martial_melee"},
            "effects": [{"type": "damage", "damage_dice": "1d8+3", "damage_type": "slashing", "ability": "strength"}],
            "resources": [{"type": "action_economy", "category": "standard", "action_type": "attack"}]
        }

        AOE spell with save:
        {
            "id": "fireball",
            "name": "Fireball",
            "description": "Hurl an explosive ball of flame",
            "type": "cast_spell",
            "category": "standard",
            "targeting": "multi",
            "range": 150.0,
            "hits": 1,
            "resolution": {"type": "saving_throw", "ability": "dexterity", "use_spell_dc": true},
            "effects": [{"type": "damage", "damage_dice": "8d6", "damage_type": "fire", "half_on_save": true}],
            "resources": [
                {"type": "action_economy", "category": "standard", "action_type": "cast_spell"},
                {"type": "spell_slot", "level": 3}
            ]
        }

        Self-healing ability:
        {
            "id": "second_wind",
            "name": "Second Wind",
            "description": "Regain hit points as a bonus action",
            "type": "special",
            "category": "bonus",
            "targeting": "self",
            "range": 0.0,
            "hits": 1,
            "resolution": {"type": "auto_success"},
            "effects": [{"type": "healing", "heal_dice": "1d10+{level}"}],
            "resources": [
                {"type": "action_economy", "category": "bonus", "action_type": "special"},
                {"type": "limited_uses", "resource_name": "second_wind"}
            ]
        }
    """

    # Composable components
    conditions: list[
        Annotated[
            RequiresPriorActionCondition | ArmorRestrictionCondition | ResourceThresholdCondition,
            Discriminator("type"),
        ]
    ] = Field(
        default_factory=list,
        description=(
            "Availability conditions that must be met (e.g., requires_prior_action, armor_restriction, "
            "resource_threshold). Usually empty for simple actions."
        ),
    )
    resolution: Annotated[AutoSuccessStrategy | AttackRollStrategy | SavingThrowStrategy, Discriminator("type")] = (
        Field(
            description=(
                "How success is determined: auto_success (always succeeds), attack_roll (d20+mods vs AC), "
                "or saving_throw (target rolls save)"
            )
        )
    )
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
    ] = Field(
        default_factory=list,
        description=(
            "What happens when the action succeeds: damage, healing, apply/remove conditions, summon evocation, "
            "recover resources, etc. Can combine multiple effects."
        ),
    )
    resources: list[
        Annotated[
            ActionEconomyConsumer | SpellSlotConsumer | LimitedUsesConsumer,
            Discriminator("type"),
        ]
    ] = Field(
        default_factory=list,
        description=(
            "Resources consumed when using this action. Always include at least action_economy. "
            "May also consume spell_slots or limited_uses."
        ),
    )
    level_required: int | None = Field(
        default=1,
        description="Minimum character level required to use this action (1-20). Use None if no level requirement.",
    )

    def execute(self, actor: Character, target: Any, ctx: CombatContext) -> None:
        """Execute the action using composable primitives.

        Args:
            actor: Character performing the action
            target: Target of the action (Character for most actions, Position for evocations)
            ctx: Combat context
        """
        # Fire start events (only for Character targets)
        if not isinstance(target, Position):
            TraitService.trigger_event(actor, EventType.COMBAT_START, actor, target, ctx)
            TraitService.trigger_event(target, EventType.COMBAT_START, actor, target, ctx)

        # Handle concentration before resolving (break existing concentration if needed)
        concentration_effect = next(
            (e for e in self.effects if isinstance(e, ApplyConditionsEffect) and e.concentration),
            None,
        )
        if concentration_effect and actor.concentrating_on:
            old_effect = actor.concentrating_on
            EffectService.remove_condition(actor, old_effect.type)
            actor.log_event(f"{actor.name} stops concentrating on {old_effect.type.value}")

        # Resolve (determine success/failure)
        # For position-based targeting (evocations), skip resolution and auto-succeed
        success = True if isinstance(target, Position) else self.resolution.resolve(actor, target, ctx)

        # Apply effects (if successful, or if apply_on_failure is True)
        if success or self.resolution.apply_on_failure:
            for effect in self.effects:
                effect.apply(actor, target, ctx)

            # Set up new concentration tracking after effects are applied
            if concentration_effect and concentration_effect.conditions:
                actor.concentrating_on = concentration_effect.conditions[0]

        # Fire end events (only for Character targets)
        if not isinstance(target, Position):
            TraitService.trigger_event(actor, EventType.COMBAT_END, actor, target, ctx)
            TraitService.trigger_event(target, EventType.COMBAT_END, actor, target, ctx)

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
            if hasattr(consumer, "is_available") and isinstance(consumer, ActionEconomyConsumer):
                # Note: We need the actor, not just action_economy
                # This is a limitation - we'll need to refactor this slightly
                # For now, just check action economy consumers
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
