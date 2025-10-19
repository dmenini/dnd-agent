from agent.actions.base import Action, ActionCategory, ActionType
from agent.character.character import Character
from agent.character.resources import ActionEconomy
from agent.models.context import CombatContext
from agent.models.enums import TargetingType
from agent.models.position import Position


class MovementAction(Action):
    """Option shown to the Agent"""

    id: str = "move"
    name: str = "Movement"
    description: str = "Move on the map to a new position within the range."
    action_type: ActionType = ActionType.MOVE
    category: ActionCategory = ActionCategory.MOVEMENT

    targeting: TargetingType = TargetingType.SELF
    range: float

    def is_available(self, action_economy: ActionEconomy) -> bool:
        return action_economy.can_move(distance=self.range)

    def execute(self, actor: Character, target: Position, _: CombatContext) -> None:
        actor.move(target)

    def finalize(self, actor: Character) -> None:
        """Consume movement."""
        actor.action_economy.use_movement(distance=self.range)
