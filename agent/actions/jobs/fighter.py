from agent.actions.base import ActionType, LimitedBonusAction
from agent.character.character import Character
from agent.logs.log_event import LogLevel
from agent.models.context import CombatContext
from agent.models.enums import TargetingType
from agent.services.combat_service import CombatService
from agent.services.roll_service import RollService


class SecondWindAction(LimitedBonusAction):
    """Once per short rest, recover 1d10 + level HP."""

    id: str
    description: str
    name: str = "Second Wind"
    type: ActionType = ActionType.SPECIAL
    targeting: TargetingType = TargetingType.SELF

    def execute(self, actor: Character, target: Character, ctx: CombatContext) -> None:  # noqa: ARG002
        heal_amount = RollService.roll("1d10", character=actor).total + actor.level
        CombatService.heal(actor, heal_amount)
        actor.log_event(
            f"{actor.name} catches their breath and recovers {heal_amount} HP ({actor.attributes.hp}/{actor.max_hp}).",
            log_type=LogLevel.DETAIL,
        )
