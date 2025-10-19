from agent.actions.base import Action, ActionCategory, ActionType
from agent.character.character import Character
from agent.character.resources import ActionEconomy
from agent.models.enums import TargetingType
from agent.models.position import Position


class DashAction(Action):
    """Option shown to the Agent"""

    id: str = "dash"
    name: str = "Dash"
    description: str = "Dash on the map to a new position within double the range."
    action_type: ActionType = ActionType.DASH
    category: ActionCategory = ActionCategory.STANDARD

    targeting: TargetingType = TargetingType.SELF
    range: float

    def is_available(self, action_economy: ActionEconomy) -> bool:
        return action_economy.can_use_standard(self.action_type) and action_economy.can_move(self.range)

    def execute(self, actor: Character, target: Position) -> None:
        actor.move(target)

    def finalize(self, actor: Character) -> None:
        """Consume standard action point and movement."""
        super().finalize(actor)
        actor.action_economy.use_movement(distance=self.range)
