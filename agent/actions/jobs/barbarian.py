from agent.actions.base import ActionType, LimitedBonusAction
from agent.character.character import Character
from agent.effects.status_effects.enraged import Enraged
from agent.equipment.armor import ArmorType
from agent.logs.log_event import LogLevel
from agent.models.context import CombatContext
from agent.models.enums import TargetingType


class RageAction(LimitedBonusAction):
    """
    In battle, you fight with primal ferocity. On your turn, you can enter a rage as a bonus action.
    While raging, you gain the following benefits if you aren't wearing heavy armor:
    * You have advantage on Strength checks and Strength saving throws.
    * When you make a melee weapon attack using Strength, you gain a bonus to the damage roll.
    * You have resistance to bludgeoning, piercing, and slashing damage.
    * If you are able to cast spells, you can't cast them or concentrate on them while raging.

    Your rage lasts for 1 turn. It ends early if you are knocked unconscious,
    or if your turn ends and you haven't attacked a hostile creature since your last turn,
    or taken damage since then. You can also end your rage on your turn as a bonus action.
    """

    # TODO: Implement early stop conditions

    id: str
    description: str
    name: str = "Rage"
    type: ActionType = ActionType.SPECIAL
    targeting: TargetingType = TargetingType.SELF
    damage_bonus: int

    def execute(self, actor: Character, target: Character, ctx: CombatContext) -> None:  # noqa: ARG002
        if not actor.armor or actor.armor.armor_type != ArmorType.HEAVY:
            effect = Enraged(duration=1, damage_bonus=self.damage_bonus)
            actor.apply_effect(effect)
            actor.log_event(f"{actor.name} enters a furious rage!", log_type=LogLevel.DETAIL)
        else:
            actor.log_event(
                f"{actor.name} fails to enter rage because it's wearing heavy armor...", log_type=LogLevel.DETAIL
            )
