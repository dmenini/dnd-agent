from agent.actions.base import ActionType, LimitedBonusAction
from agent.character.abilities import AbilityType
from agent.character.character import Character
from agent.effects.status_effects.base import StatusEffect, StatusType
from agent.effects.traits import TraitBuilder
from agent.equipment.armor import ArmorType
from agent.logs.log_event import LogLevel
from agent.models.context import CombatContext
from agent.models.damage import DamageType
from agent.models.enums import TargetingType
from agent.services.effect_service import EffectService


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
            effect = StatusEffect(
                type=StatusType.ENRAGED,
                save_dc=0,
                traits=[
                    TraitBuilder.advantage_on_save(source_id=StatusType.ENRAGED.value, ability=AbilityType.STR),
                    TraitBuilder.resistance(source_id=StatusType.ENRAGED.value, damage_type=DamageType.BLUDGEONING),
                    TraitBuilder.resistance(source_id=StatusType.ENRAGED.value, damage_type=DamageType.PIERCING),
                    TraitBuilder.resistance(source_id=StatusType.ENRAGED.value, damage_type=DamageType.SLASHING),
                    TraitBuilder.melee_damage_bonus(source_id=StatusType.ENRAGED.value, value=self.damage_bonus),
                ],
                duration=1,
            )
            EffectService.apply_condition(actor, effect)
            actor.log_event(f"{actor.name} enters a furious rage!", log_type=LogLevel.DETAIL)
        else:
            actor.log_event(
                f"{actor.name} fails to enter rage because it's wearing heavy armor...", log_type=LogLevel.DETAIL
            )
