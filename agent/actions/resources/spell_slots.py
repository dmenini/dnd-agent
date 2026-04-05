"""Spell slot resource consumer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from agent.actions.resources.base import ResourceConsumer
from agent.character.resources import SpellLevel

if TYPE_CHECKING:
    from agent.character.character import Character


class SpellSlotConsumer(ResourceConsumer):
    """Consume spell slots.

    Used by all spells that cost spell slots (cantrips don't consume slots).
    """

    level: SpellLevel

    def consume(self, actor: Character) -> None:
        """Consume spell slot from actor."""
        if self.level != SpellLevel.CANTRIP:
            actor.spell_slots.consume(self.level)

    def is_available(self, actor: Character) -> bool:
        """Check if actor has spell slot available."""
        if self.level == SpellLevel.CANTRIP:
            return True  # Cantrips don't require slots
        return actor.spell_slots.available(self.level) > 0
