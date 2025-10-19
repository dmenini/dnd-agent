from agent.character.character import Character
from agent.effects.base import StatusEffect
from agent.logs.events import EventType, Icon


class CharacterManager:
    def __init__(self, character: Character) -> None:
        self.character = character

    def start_turn(self) -> None:
        self.character.log_event(f"{self.character.name} starts turn", event_type=EventType.DEBUG)
        self.character.turn_done = False
        self.character.action_economy.restore_turn()
        self._try_expire_effects(is_start=True)

    def end_turn(self) -> None:
        self.character.log_event(f"{self.character.name} ends turn", event_type=EventType.DEBUG)
        self._try_expire_effects(is_start=False)
        self.character.turn_done = True

    def end_round(self) -> None:
        self.character.action_economy.restore_reaction()

    def try_apply_status(self, effect: StatusEffect) -> bool:
        """Apply status effect in case there are no immunities and save throw fails."""
        # Check immunity
        if self.character.is_immune_to(effect.type):
            self.character.log_event(f"{self.character.name} is immune to {effect.type.value} effect")
            return False

        # Saving throw
        if effect.save_dc:
            roll = self.character.save_roll(save_stat=effect.save_stat)
            self.character.log_event(
                f"{effect.save_stat.name} save throw: {roll.total} vs DC {effect.save_dc}", icon=Icon.ROLL
            )

            if roll.total >= effect.save_dc:
                # Negate effect
                self.character.log_event(f"{self.character.name} resists being {effect.type.value}!", icon=Icon.DEFENSE)
                return False

        # Apply the effect
        self.apply_status(effect)

        return True

    def apply_status(self, effect: StatusEffect) -> None:
        """Apply status effect, overriding any ongoing status effect of same type."""
        existing_effect = next((eff for eff in self.character.status_effects if eff.type == effect.type), None)

        if not existing_effect:
            # No existing effect -> just apply it
            self.character.status_effects.append(effect)
            effect.on_apply(self.character)
            self.character.log_event(f"{self.character.name} is {effect}", icon=Icon.EFFECT_APPLIED)
            return

        # There is already an effect of this type -> remove old one, apply new
        existing_effect.on_expire(self.character)
        self.character.status_effects.remove(existing_effect)
        self.character.status_effects.append(effect)
        effect.on_apply(self.character)
        self.character.log_event(f"{self.character.name} is again {effect}", icon=Icon.EFFECT_APPLIED)

    def _try_expire_effects(self, *, is_start: bool = True) -> None:
        # Copy the list since effects may modify self.status_effects in-place
        for effect in list(self.character.status_effects):
            if is_start:
                effect.duration -= 1
                effect.on_turn_start(self.character)
            else:
                effect.on_turn_end(self.character)
            if effect.is_expired():
                effect.on_expire(self.character)
                self.character.log_event(
                    f"{self.character.name} is not {effect.type.value} anymore!", icon=Icon.EFFECT_EXPIRED
                )

        # Remove expired effects
        self.character.status_effects = [e for e in self.character.status_effects if not e.is_expired()]
