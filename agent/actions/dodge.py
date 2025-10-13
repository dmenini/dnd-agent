from agent.actions.base import Action
from agent.models.enums import ActionCategory, ActionType, TargetingType


class DodgeAction(Action):
    """Option shown to the Agent"""

    id: str = "dodge"
    name: str = "Dodge"
    description: str = "Prepare to dodge in the next turn."
    action_type: ActionType = ActionType.DODGE
    category: ActionCategory = ActionCategory.STANDARD

    targeting: TargetingType = TargetingType.SELF
