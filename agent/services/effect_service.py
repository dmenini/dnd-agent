from typing import TYPE_CHECKING

from agent.logs.log_event import Icon
from agent.models.enums import EventType
from agent.services.roll_service import RollService

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.effects.status_effects.base import StatusEffect, StatusType


class EffectService:
    """Stateless service for managing character status effects."""

    @classmethod
    def is_immune_to(cls, character: "Character", condition: "StatusType") -> bool:  # noqa: ARG003
        """Check if character is immune to a condition."""
        # TODO: Implement this
        return False

    @classmethod
    def has_condition(cls, character: "Character", condition: "StatusType") -> bool:
        """Check if character has a specific condition."""
        return any(c.type == condition for c in character.status_effects)

    @classmethod
    def try_apply_condition(cls, character: "Character", condition: "StatusEffect") -> bool:
        """Apply status effect if not immune and save throw fails."""
        # Check immunity
        if cls.is_immune_to(character, condition.type):
            character.log_event(f"{character.name} is immune to {condition.type.value} effect")
            return False

        # Saving throw
        if condition.save_dc:
            roll = RollService.save_roll(character, ability=condition.save_ability)
            character.log_event(
                f"{condition.save_ability.name} save throw: {roll.total} vs DC {condition.save_dc}", icon=Icon.ROLL
            )

            if roll.total >= condition.save_dc:
                # Negate effect
                character.log_event(f"{character.name} resists being {condition.type.value}!", icon=Icon.DEFENSE)
                return False

        # Apply the effect
        cls.apply_condition(character, condition)

        return True

    @classmethod
    def apply_condition(cls, character: "Character", condition: "StatusEffect") -> None:
        """Apply status effect, overriding any ongoing status effect of same type."""
        existing_status = next((eff for eff in character.status_effects if eff.type == condition.type), None)

        if not existing_status:
            # No existing effect → just apply it
            character.status_effects.append(condition)
            condition.on_apply(character)
            character.log_event(f"{character.name} is {condition}", icon=Icon.EFFECT_APPLIED)
            return

        # There is already an effect of this type → remove old one, apply new
        existing_status.on_expire(character)
        character.status_effects.remove(existing_status)
        character.status_effects.append(condition)
        condition.on_apply(character)
        character.log_event(f"{character.name} is again {condition}", icon=Icon.EFFECT_APPLIED)

    @classmethod
    def remove_condition(cls, character: "Character", condition: "StatusType") -> None:
        """Remove a condition by type."""
        character.status_effects = [e for e in character.status_effects if e.type != condition]
        character.log_event(f"{character.name} is not {condition.value} anymore!", icon=Icon.EFFECT_EXPIRED)

    @classmethod
    def try_expire_conditions(cls, character: "Character", *, is_start: bool = True) -> None:
        """Decrement condition durations and remove expired ones."""
        # Copy the list since effects may modify character.status_effects in-place
        for condition in list(character.status_effects):
            if is_start:
                condition.duration -= 1
                character.trigger_event(EventType.TURN_START, character)
                if condition.save_mode == "start":
                    cls._try_break_free(character, condition)
            else:
                character.trigger_event(EventType.TURN_END, character)

            if condition.is_expired():
                condition.on_expire(character)
                character.log_event(
                    f"{character.name} is not {condition.type.value} anymore!", icon=Icon.EFFECT_EXPIRED
                )
                if condition.followup:
                    cls.try_apply_condition(character, condition.followup)

        # Remove expired effects
        character.status_effects = [e for e in character.status_effects if not e.is_expired()]

    @classmethod
    def _try_break_free(cls, character: "Character", condition: "StatusEffect") -> None:
        """Attempt to break free from a condition via save throw."""
        roll = RollService.save_roll(character, ability=condition.save_ability)
        if roll.total >= condition.save_dc:
            condition.duration = 0
