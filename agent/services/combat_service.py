"""Combat service - stateless combat operations and turn lifecycle."""

from typing import TYPE_CHECKING

from agent.logs.log_event import Icon
from agent.models.position import Position
from agent.services.effect_service import EffectService
from agent.services.evocation_service import EvocationService

if TYPE_CHECKING:
    from agent.character.character import Character


class CombatService:
    """Stateless service for combat operations and turn management.

    Handles damage/healing, movement, and turn lifecycle.
    Replaces scattered combat methods and TurnService.
    """

    @classmethod
    def apply_damage(cls, character: "Character", damage: int) -> None:
        """Apply damage to a character.

        Args:
            character: The character taking damage
            damage: Amount of damage to apply
        """
        character.attributes.hp = max(0, character.attributes.hp - damage)

    @classmethod
    def heal(cls, character: "Character", amount: int) -> None:
        """Heal a character.

        Args:
            character: The character to heal
            amount: Amount of HP to restore
        """
        character.attributes.hp = min(character.attributes.hp + amount, character.max_hp)

    @classmethod
    def move(cls, character: "Character", destination: Position) -> None:
        """Move a character to a new position.

        Args:
            character: The character to move
            destination: Target position
        """
        starting_pos = character.combat.pos.model_copy()
        character.combat.pos = destination
        character.log_event(f"{character.name} moves from {starting_pos} to {destination}", icon=Icon.MOVE)

    @classmethod
    def is_dead(cls, character: "Character") -> bool:
        """Check if a character is dead.

        Args:
            character: The character to check

        Returns:
            True if character's HP is 0 or less
        """
        return character.attributes.hp <= 0

    # Turn lifecycle methods (from TurnService)

    @classmethod
    def start_turn(cls, character: "Character") -> None:
        """Start a character's turn - restore action economy and expire start-of-turn effects.

        Args:
            character: The character starting their turn
        """
        character.combat.turn_done = False
        character.combat.action_economy.restore_turn()
        EffectService.try_expire_conditions(character, is_start=True)
        EvocationService.expire_evocations(character)

    @classmethod
    def end_turn(cls, character: "Character") -> None:
        """End a character's turn - expire end-of-turn effects.

        Args:
            character: The character ending their turn
        """
        EffectService.try_expire_conditions(character, is_start=False)
        character.combat.turn_done = True

    @classmethod
    def end_round(cls, character: "Character") -> None:
        """End a round for a character - restore reactions.

        Args:
            character: The character ending their round
        """
        character.combat.action_economy.restore_reaction()

    @classmethod
    def end_combat(cls, character: "Character") -> None:
        """End combat for a character - rest abilities.

        Args:
            character: The character ending combat
        """
        # TODO: This should be done on rest
        for ability in character.special_abilities:
            if hasattr(ability, "rest"):
                ability.rest()
