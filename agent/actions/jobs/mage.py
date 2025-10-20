import math

from agent.actions.base import Action, ActionCategory, ActionType
from agent.character.character import Character
from agent.logs.events import LogLevel


class ArcaneRecoveryAction(Action):
    """
    Once per short rest, recover expended spell slots up to a combined level
    equal to half your Mage level (rounded up).
    """

    id: str
    name: str = "Arcane Recovery"
    description: str
    action_type: ActionType = ActionType.SPECIAL
    category: ActionCategory = ActionCategory.BONUS
    uses_per_rest: int = 1  # TODO: implement this new resource

    def execute(self, actor: Character, target: Character) -> None:  # noqa: ARG002
        """Recover spell slots based on half the caster's level."""
        max_recovery = math.ceil(actor.level / 2)
        recovered = 0

        # Iterate over spell slots from highest to lowest
        for level in sorted(actor.spell_slots.slots.keys(), key=lambda x: x.value, reverse=True):
            current = actor.spell_slots.slots[level]
            maximum = actor.spell_slots.max_slots[level]

            if current < maximum:
                slots_to_recover = min(maximum - current, max_recovery - recovered)
                if slots_to_recover <= 0:
                    continue

                actor.spell_slots.slots[level] += slots_to_recover
                recovered += slots_to_recover

                actor.log_event(
                    f"{actor.name} recovers {slots_to_recover} level {level} spell slot(s).",
                    event_type=LogLevel.DETAIL,
                )

                if recovered >= max_recovery:
                    break

        if recovered == 0:
            actor.log_event(
                f"{actor.name} has no spell slots to recover.",
                event_type=LogLevel.DETAIL,
            )

    def finalize(self, actor: Character) -> None:
        """Consume one use of Arcane Recovery."""
        if self.uses_per_rest > 0:
            self.uses_per_rest -= 1
        actor.action_economy.use_bonus(self.action_type)
