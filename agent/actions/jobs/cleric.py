from agent.actions.base import ActionType, LimitedBonusAction
from agent.character.character import Character
from agent.logs.log_event import LogLevel
from agent.models.context import CombatContext
from agent.models.enums import TargetingType
from agent.services.roll_service import RollService


class DivineRestorationAction(LimitedBonusAction):
    """Once per combat, channel divine power to heal allies."""

    id: str
    description: str
    name: str = "Divine Restoration"
    type: ActionType = ActionType.SPECIAL
    targeting: TargetingType = TargetingType.MULTI

    def execute(self, actor: Character, target: Character, ctx: CombatContext) -> None:  # noqa: ARG002
        # TODO: Should run on all allies
        heal_roll = RollService.heal_roll(actor, expr="1d10")
        heal_amount = heal_roll.total + actor.level // 2
        heal_amount = min(heal_amount, target.max_hp - target.attributes.hp)
        target.heal(heal_amount)
        actor.log_event(
            f"{actor.name} channels divine light to heal {target.name} "
            f"for {heal_amount} HP ({target.attributes.hp}/{target.max_hp}).",
            log_type=LogLevel.DETAIL,
        )


class PreserveLifeAction(LimitedBonusAction):
    """Restore a number of hit points equal to five times your cleric level.
    Choose any creatures within 30 feet of you, and divide those hit points among them.
    This feature can restore a creature to no more than half of its hit point maximum.
    You can't use this feature on an undead or a construct.
    """

    id: str
    description: str
    name: str = "Preserve Life"
    type: ActionType = ActionType.SPECIAL
    targeting: TargetingType = TargetingType.ALLIES
    range: int = 30

    def execute(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        total = actor.level * 5
        num_targets = len([val for val in ctx.hits.values() if val > 0])
        heal_amount = min(total // num_targets, target.max_hp // 2, target.max_hp - target.attributes.hp)
        target.heal(heal_amount)
        actor.log_event(
            f"{actor.name} channels divine light to heal {target.name} "
            f"for {heal_amount} HP ({target.attributes.hp}/{target.max_hp}).",
            log_type=LogLevel.DETAIL,
        )
