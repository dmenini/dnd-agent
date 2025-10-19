from typing import Any

from agent.actions.base import Action, ActionCategory, ActionType
from agent.character.character import Character
from agent.character.manager import CharacterManager
from agent.effects.dodge import Dodge
from agent.models.enums import TargetingType


class DodgeAction(Action):
    """Option shown to the Agent"""

    id: str = "dodge"
    name: str = "Dodge"
    description: str = "Prepare to dodge in the next turn."
    action_type: ActionType = ActionType.DODGE
    category: ActionCategory = ActionCategory.STANDARD

    targeting: TargetingType = TargetingType.SELF

    def execute(self, actor: Character, target: Any) -> None:  # noqa: ARG002
        effect = Dodge(duration=1)
        manager = CharacterManager(character=actor)
        manager.apply_status(effect)
