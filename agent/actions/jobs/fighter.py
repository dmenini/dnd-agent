from agent.actions.base import Action, ActionCategory, ActionType
from agent.character.character import Character
from agent.logs.events import LogLevel


class SecondWindAction(Action):
    id: str
    description: str
    name: str
    action_type: ActionType = ActionType.SPECIAL
    category: ActionCategory = ActionCategory.BONUS
    uses_per_rest: int = 1  # TODO: implement this as uses_per_combat

    def execute(self, actor: Character, target: Character) -> None:  # noqa: ARG002
        heal_amount = actor.damage_roll(expr="1d10").total + actor.level
        actor.heal(heal_amount)
        actor.log_event(f"{actor.name} heals {heal_amount} HP.", event_type=LogLevel.DETAIL)

    def finalize(self, actor: Character) -> None:
        """Consume resources."""
        actor.action_economy.use_bonus(self.action_type)
