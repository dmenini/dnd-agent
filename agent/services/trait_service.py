"""Trait service - stateless trait and passive management."""

from typing import TYPE_CHECKING, Any

from agent.effects.base import normalize_id, Trait
from agent.logs.log_event import LogLevel
from agent.models.enums import EventType, FeatureId

if TYPE_CHECKING:
    from agent.character.character import Character


class TraitService:
    """Stateless service for managing traits, passives, and event-driven behavior.

    Handles registration/unregistration of passive traits,
    triggering events, and state change notifications.
    """

    @classmethod
    def register_passive(cls, character: "Character", trait: Trait) -> None:
        """Register a passive trait (idempotent).

        Args:
            character: The character gaining the trait
            trait: The trait to register
        """
        # Add to passives list if not already there
        if all(trait.id != p.id for p in character.passives):
            character.passives.append(trait)
            character.log_event(f"{character.name} gained passive trait {trait.name}", log_type=LogLevel.DETAIL)

        # Apply immediately if it's a modifier (even if passive exists, as serialization loses modifiers)
        if trait.event_type == EventType.MODIFIER:
            trait.apply(character)

    @classmethod
    def unregister_passive(cls, character: "Character", feature_id: FeatureId, source_id: str) -> None:
        """Unregister a passive trait.

        Args:
            character: The character losing the trait
            feature_id: The feature ID of the trait
            source_id: The source ID of the trait
        """
        source_id = normalize_id(source_id)
        matching_traits = [
            t for t in character.passives if t.feature_id == feature_id and t.source_id == source_id
        ]

        for trait in matching_traits:
            # Remove modifier if applicable
            if trait.event_type == EventType.MODIFIER:
                character.attributes.remove_modifier(trait.id)

            # Remove from passives
            character.passives.remove(trait)

            character.log_event(f"{character.name} lost passive trait {trait.name}", log_type=LogLevel.DETAIL)

    @classmethod
    def trigger_event(cls, character: "Character", event: EventType, *args: Any, **kwargs: Any) -> None:
        """Trigger all listeners for the given event type in priority order.

        Args:
            character: The character whose traits should be triggered
            event: The event type to trigger
            *args: Positional arguments to pass to trait handlers
            **kwargs: Keyword arguments to pass to trait handlers
        """
        listeners = [trait for trait in character.passives if trait.event_type == event]
        listeners.sort(key=lambda t: t.priority)

        for trait in list(listeners):
            trait.apply(*args, **kwargs)

    @classmethod
    def notify_state_change(cls, character: "Character", field_name: str) -> None:
        """Called whenever an internal property changes.

        Re-applies conditional traits that depend on the changed field.

        Args:
            character: The character whose state changed
            field_name: The name of the field that changed
        """
        # Find all traits that depend on this field
        dependent_traits = [
            trait
            for trait in character.passives
            if trait.event_type == EventType.MODIFIER and trait.condition_depends_on(field_name)
        ]

        # Re-apply them (they'll check their conditions)
        for trait in dependent_traits:
            trait.apply(character)
