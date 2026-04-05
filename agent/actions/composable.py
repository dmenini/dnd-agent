"""Composable action system."""

from __future__ import annotations

from typing import Annotated, Any
from typing import TYPE_CHECKING

from pydantic import Field

from agent.actions.base import Action, ActionCategory, ActionType
from agent.actions.effects.base import EffectApplicator
from agent.actions.resources.base import ResourceConsumer
from agent.actions.strategies.base import ResolutionStrategy
from agent.models.enums import EventType, TargetingType
from agent.services.trait_service import TraitService

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.character.resources import ActionEconomy
    from agent.models.context import CombatContext


class ComposableAction(Action):
    """Data-driven action using composable primitives.

    Every action is composed of:
    1. Resolution strategy (how to determine success/failure)
    2. Effect applicators (what happens on success)
    3. Resource consumers (what it costs)

    This allows defining abilities as JSON data instead of Python classes.
    """

    # Composable components (THE KEY TO DATA-DRIVEN ABILITIES!)
    resolution: ResolutionStrategy
    effects: list[EffectApplicator] = Field(default_factory=list)
    resources: list[ResourceConsumer] = Field(default_factory=list)

    def execute(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        """Execute the action using composable primitives."""
        # Fire start events
        TraitService.trigger_event(actor, EventType.COMBAT_START, actor, target, ctx)
        TraitService.trigger_event(target, EventType.COMBAT_START, actor, target, ctx)

        # Resolve (determine success/failure)
        success = self.resolution.resolve(actor, target, ctx)

        # Apply effects (if successful, or if apply_on_failure is True)
        if success or self.resolution.apply_on_failure:
            for effect in self.effects:
                effect.apply(actor, target, ctx)

        # Fire end events
        TraitService.trigger_event(actor, EventType.COMBAT_END, actor, target, ctx)
        TraitService.trigger_event(target, EventType.COMBAT_END, actor, target, ctx)

    def finalize(self, actor: Character) -> None:
        """Consume resources after action execution."""
        for consumer in self.resources:
            consumer.consume(actor)

    def is_available(self, action_economy: ActionEconomy) -> bool:
        """Check if action is available (has resources and action economy)."""
        # Check action economy
        for consumer in self.resources:
            if hasattr(consumer, "is_available"):
                # Note: We need the actor, not just action_economy
                # This is a limitation - we'll need to refactor this slightly
                # For now, just check action economy consumers
                from agent.actions.resources.action_economy import ActionEconomyConsumer
                if isinstance(consumer, ActionEconomyConsumer):
                    if self.category == ActionCategory.STANDARD:
                        return action_economy.can_use_standard(self.type)
                    elif self.category == ActionCategory.BONUS:
                        return action_economy.can_use_bonus(self.type)
                    elif self.category == ActionCategory.REACTION:
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
ActionDefinition = Annotated[
    ComposableAction,
    Field(discriminator="category")
]
