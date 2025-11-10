from agent.actions.base import ActionType, LimitedBonusAction
from agent.character.character import Character
from agent.logs.log_event import LogLevel
from agent.models.context import CombatContext
from agent.models.enums import TargetingType


class DivineRestorationAction(LimitedBonusAction):
    """Once per combat, channel divine power to heal allies."""

    id: str
    description: str
    name: str = "Second Wind"
    type: ActionType = ActionType.SPECIAL
    targeting: TargetingType = TargetingType.MULTI

    def execute(self, actor: Character, target: Character, ctx: CombatContext) -> None:  # noqa: ARG002
        # TODO: Should run on all allies
        heal_roll = actor.heal_roll(expr="1d10")
        heal_amount = heal_roll.total + actor.level // 2
        heal_amount = min(heal_amount, target.max_hp - target.attributes.hp)
        target.heal(heal_amount)
        actor.log_event(
            f"{actor.name} channels divine energy to heal {target.name} "
            f"for {heal_amount} HP ({target.attributes.hp}/{target.max_hp}).",
            log_type=LogLevel.DETAIL,
        )
