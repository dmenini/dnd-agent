from agent.actions.base import ActionType, LimitedBonusAction
from agent.character.character import Character
from agent.logs.events import LogLevel


class SecondWindAction(LimitedBonusAction):
    """Once per short rest, recover 1d10 + level HP."""

    id: str
    description: str
    name: str = "Second Wind"
    action_type: ActionType = ActionType.SPECIAL

    def execute(self, actor: Character, target: Character) -> None:  # noqa: ARG002
        heal_amount = actor.damage_roll(expr="1d10").total + actor.level
        actor.heal(heal_amount)
        actor.log_event(f"{actor.name} heals {heal_amount} HP.", event_type=LogLevel.DETAIL)
