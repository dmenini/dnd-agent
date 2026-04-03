from typing import TYPE_CHECKING

from agent.services.effect_service import EffectService
from agent.services.evocation_service import EvocationService

if TYPE_CHECKING:
    from agent.character.character import Character


class TurnService:
    """Stateless service for managing character turn lifecycle."""

    @classmethod
    def start_turn(cls, character: "Character") -> None:
        """Start a character's turn - restore action economy and expire start-of-turn effects."""
        character.turn_done = False
        character.action_economy.restore_turn()
        EffectService.try_expire_conditions(character, is_start=True)
        EvocationService.expire_evocations(character)

    @classmethod
    def end_turn(cls, character: "Character") -> None:
        """End a character's turn - expire end-of-turn effects."""
        EffectService.try_expire_conditions(character, is_start=False)
        character.turn_done = True

    @classmethod
    def end_round(cls, character: "Character") -> None:
        """End a round for a character - restore reactions."""
        character.action_economy.restore_reaction()

    @classmethod
    def end_combat(cls, character: "Character") -> None:
        """End combat for a character - rest abilities."""
        # TODO: This should be done on rest
        for ability in character.special_abilities:
            if hasattr(ability, "rest"):
                ability.rest()
