from typing import TYPE_CHECKING

from agent.actions.base import Action

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.effects.evocations.base import Evocation


class EvocationService:
    """Stateless service for managing character evocations (summoned entities)."""

    @classmethod
    def add_evocation(cls, character: "Character", evo: "Evocation") -> None:
        """Add or replace an evocation."""
        existing = next((e for e in character.evocations if e.source_id == evo.source_id), None)

        if not existing:
            character.evocations.append(evo)
            return

        # There is already an evocation of this type → remove old one, apply new
        cls.remove_evocation(character, evo.source_id)
        character.evocations.append(evo)

    @classmethod
    def remove_evocation(cls, character: "Character", source_id: str) -> None:
        """Remove an evocation by source ID."""
        character.evocations = [e for e in character.evocations if e.source_id != source_id]

    @classmethod
    def expire_evocations(cls, character: "Character") -> None:
        """Decrement evocation durations and remove expired ones."""
        for evo in list(character.evocations):
            evo.duration -= 1
            evo.action_economy.restore_turn()
            if evo.is_expired():
                cls.remove_evocation(character, evo.source_id)

    @classmethod
    def evocation_actions(cls, character: "Character") -> list[Action]:
        """Get all actions available from character's evocations."""
        actions = []
        for evo in character.evocations:
            actions.extend(evo.available_actions())
        return actions
