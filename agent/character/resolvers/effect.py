from typing import TYPE_CHECKING, cast

from pydantic import Field

from agent.character.resolvers.base import CharacterBase
from agent.effects.status_effects.base import StatusEffect, StatusType
from agent.logs.log_event import Icon
from agent.models.enums import EventType
from agent.services.roll_service import RollService

if TYPE_CHECKING:
    from agent.character.character import Character


class EffectResolver(CharacterBase):
    status_effects: list[StatusEffect] = Field(default_factory=list)

    def is_immune_to(self, condition: StatusType) -> bool:  # noqa: ARG002
        # TODO: Implement this
        return False

    def has_condition(self, condition: StatusType) -> bool:
        return any(c.type == condition for c in self.status_effects)

    def try_apply_condition(self, condition: StatusEffect) -> bool:
        """Apply status effect in case there are no immunities and save throw fails."""
        # Check immunity
        if self.is_immune_to(condition.type):
            self.log_event(f"{self.name} is immune to {condition.type.value} effect")
            return False

        # Saving throw
        if condition.save_dc:
            roll = RollService.save_roll(cast("Character", self), ability=condition.save_ability)
            self.log_event(
                f"{condition.save_ability.name} save throw: {roll.total} vs DC {condition.save_dc}", icon=Icon.ROLL
            )

            if roll.total >= condition.save_dc:
                # Negate effect
                self.log_event(f"{self.name} resists being {condition.type.value}!", icon=Icon.DEFENSE)
                return False

        # Apply the effect
        self.apply_condition(condition)

        return True

    def apply_condition(self, condition: StatusEffect) -> None:
        """Apply status effect, overriding any ongoing status effect of same type."""
        existing_status = next((eff for eff in self.status_effects if eff.type == condition.type), None)

        if not existing_status:
            # No existing effect → just apply it
            self.status_effects.append(condition)
            condition.on_apply(self)
            self.log_event(f"{self.name} is {condition}", icon=Icon.EFFECT_APPLIED)
            return

        # There is already an effect of this type → remove old one, apply new
        existing_status.on_expire(self)
        self.status_effects.remove(existing_status)
        self.status_effects.append(condition)
        condition.on_apply(self)
        self.log_event(f"{self.name} is again {condition}", icon=Icon.EFFECT_APPLIED)

    def remove_condition(self, condition: StatusType) -> None:
        self.status_effects = [e for e in self.status_effects if e.type != condition]
        self.log_event(f"{self.name} is not {condition.value} anymore!", icon=Icon.EFFECT_EXPIRED)

    def try_expire_conditions(self, *, is_start: bool = True) -> None:
        # Copy the list since effects may modify self.status_effects in-place
        for condition in list(self.status_effects):
            if is_start:
                condition.duration -= 1
                self.trigger_event(EventType.TURN_START, self)
                if condition.save_mode == "start":
                    self._try_break_free(condition)
            else:
                self.trigger_event(EventType.TURN_END, self)

            if condition.is_expired():
                condition.on_expire(self)
                self.log_event(f"{self.name} is not {condition.type.value} anymore!", icon=Icon.EFFECT_EXPIRED)
                if condition.followup:
                    self.try_apply_condition(condition.followup)

        # Remove expired effects
        self.status_effects = [e for e in self.status_effects if not e.is_expired()]

    def _try_break_free(self, condition: StatusEffect) -> None:
        roll = RollService.save_roll(cast("Character", self), ability=condition.save_ability)
        if roll.total >= condition.save_dc:
            condition.duration = 0
