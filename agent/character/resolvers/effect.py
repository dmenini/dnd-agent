from agent.character.resolvers.base import CharacterBase
from agent.effects.status_effects.base import EffectType, StatusEffect
from agent.logs.log_event import Icon
from agent.models.constants import EventType


class EffectResolver(CharacterBase):
    status_effects: list[StatusEffect] = []

    def is_immune_to(self, cond: EffectType) -> bool:  # noqa: ARG002
        # TODO: Implement this
        return False

    def try_apply_effect(self, effect: StatusEffect) -> bool:
        """Apply status effect in case there are no immunities and save throw fails."""
        # Check immunity
        if self.is_immune_to(effect.type):
            self.log_event(f"{self.name} is immune to {effect.type.value} effect")
            return False

        # Saving throw
        if effect.save_dc:
            roll = self.save_roll(ability=effect.save_ability)
            self.log_event(
                f"{effect.save_ability.name} save throw: {roll.total} vs DC {effect.save_dc}", icon=Icon.ROLL
            )

            if roll.total >= effect.save_dc:
                # Negate effect
                self.log_event(f"{self.name} resists being {effect.type.value}!", icon=Icon.DEFENSE)
                return False

        # Apply the effect
        self.apply_effect(effect)

        return True

    def apply_effect(self, effect: StatusEffect) -> None:
        """Apply status effect, overriding any ongoing status effect of same type."""
        existing_effect = next((eff for eff in self.status_effects if eff.type == effect.type), None)

        if not existing_effect:
            # No existing effect → just apply it
            self.status_effects.append(effect)
            effect.on_apply(self)
            self.log_event(f"{self.name} is {effect}", icon=Icon.EFFECT_APPLIED)
            return

        # There is already an effect of this type → remove old one, apply new
        existing_effect.on_expire(self)
        self.status_effects.remove(existing_effect)
        self.status_effects.append(effect)
        effect.on_apply(self)
        self.log_event(f"{self.name} is again {effect}", icon=Icon.EFFECT_APPLIED)

    def try_expire_effects(self, *, is_start: bool = True) -> None:
        # Copy the list since effects may modify self.status_effects in-place
        for effect in list(self.status_effects):
            if is_start:
                effect.duration -= 1
                # if not effect.is_expired():
                self.trigger_event(EventType.TURN_START, self)
                if effect.save_mode == "start":
                    self._try_break_free(effect)
            else:
                self.trigger_event(EventType.TURN_END, self)

            if effect.is_expired():
                effect.on_expire(self)
                self.log_event(f"{self.name} is not {effect.type.value} anymore!", icon=Icon.EFFECT_EXPIRED)
                if effect.followup:
                    self.try_apply_effect(effect.followup)

        # Remove expired effects
        self.status_effects = [e for e in self.status_effects if not e.is_expired()]

    def _try_break_free(self, effect: StatusEffect) -> None:
        roll = self.save_roll(ability=effect.save_ability)
        if roll.total >= effect.save_dc:
            effect.duration = 0
