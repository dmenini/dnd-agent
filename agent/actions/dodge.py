from typing import Any

from agent.actions.base import Action, ActionCategory, ActionType
from agent.character.character import Character
from agent.effects.dodge import Dodge
from agent.models.context import CombatContext
from agent.models.enums import TargetingType
from agent.systems.character_controller import CharacterController


class DodgeAction(Action):
    """Option shown to the Agent"""

    id: str = "dodge"
    name: str = "Dodge"
    description: str = "Prepare to dodge in the next turn."
    action_type: ActionType = ActionType.DODGE
    category: ActionCategory = ActionCategory.STANDARD

    targeting: TargetingType = TargetingType.SELF

    def execute(self, actor: Character, target: Any, ctx: CombatContext) -> None:  # noqa: ARG002
        effect = Dodge(duration=1)
        controller = CharacterController(character=actor, dice=ctx.dice)
        controller.apply_status(effect)
