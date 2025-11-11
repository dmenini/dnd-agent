from agent.actions.base import ActionType, LimitedBonusAction
from agent.character.character import Character
from agent.effects.status_effects.enraged import Enraged
from agent.logs.log_event import LogLevel
from agent.models.context import CombatContext
from agent.models.enums import TargetingType


class RageAction(LimitedBonusAction):
    """Enter a rage as a bonus action to gain advantage on STR checks and bonus melee damage."""

    id: str
    description: str
    name: str = "Rage"
    type: ActionType = ActionType.SPECIAL
    targeting: TargetingType = TargetingType.SELF

    def execute(self, actor: Character, target: Character, ctx: CombatContext) -> None:  # noqa: ARG002
        effect = Enraged(duration=1)
        actor.apply_effect(effect)
        actor.log_event(f"{actor.name} enters a furious rage!", log_type=LogLevel.DETAIL)
