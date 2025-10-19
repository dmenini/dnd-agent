from typing import Self

from agent.actions.base import Action, ActionCategory, ActionType
from agent.character.character import Character
from agent.character.resources import ActionEconomy
from agent.character.stats import StatType
from agent.effects.base import StatusEffect
from agent.equipment.weapons import RangedWeapon, Weapon, WeaponType
from agent.models.context import CombatContext
from agent.models.damage import DamageType
from agent.models.enums import TargetingType
from agent.systems.character_controller import CharacterController
from agent.systems.combat_system import CombatSystem


class AttackAction(Action):
    source: str
    targeting: TargetingType
    damage_dice: str
    damage_type: DamageType
    weapon_type: WeaponType
    stat: StatType
    range: float
    status_effects: list[StatusEffect] = []

    def execute(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        ctx.metadata = ctx.metadata | self.model_dump()
        combat = CombatSystem(dice=ctx.dice)
        is_hit = combat.resolve_attack(actor, target, ctx)

        if is_hit:
            combat.apply_damage(actor, target, ctx)

            # Try to apply status effects
            controller = CharacterController(character=target, dice=ctx.dice)
            for effect in self.status_effects:
                controller.try_apply_status(effect)


class MainHandAttackAction(AttackAction):
    id: str = "main_hand_attack"
    name: str = "Main Hand Attack"
    description: str = "Base attack with main hand weapon."
    action_type: ActionType = ActionType.ATTACK
    category: ActionCategory = ActionCategory.STANDARD

    @classmethod
    def from_weapon(cls, weapon: Weapon) -> Self:
        return cls(
            source=weapon.name,
            description=f"Base Attack with main hand weapon {weapon.name}",
            weapon_type=weapon.weapon_type,
            targeting=weapon.targeting,
            damage_dice=weapon.damage_dice,
            damage_type=weapon.damage_type,
            stat=weapon.stat,
            range=weapon.range,
            status_effects=weapon.effects,
        )


class OffHandAttackAction(AttackAction):
    id: str = "off_hand_attack"
    name: str = "Off Hand Attack"
    description: str = ""
    action_type: ActionType = ActionType.OFF_HAND_ATTACK
    category: ActionCategory = ActionCategory.BONUS

    @classmethod
    def from_weapon(cls, weapon: Weapon) -> Self:
        return cls(
            source=weapon.name,
            description=f"Bonus Attack with off hand weapon {weapon.name}",
            weapon_type=weapon.weapon_type,
            targeting=weapon.targeting,
            damage_dice=weapon.damage_dice,
            damage_type=weapon.damage_type,
            stat=weapon.stat,
            range=weapon.range,
            status_effects=weapon.effects,
        )

    def is_available(self, action_economy: ActionEconomy) -> bool:
        return action_economy.bonus_actions > 0

    def finalize(self, actor: Character) -> None:
        """Consume bonus point."""
        actor.action_economy.can_use_bonus(self.action_type)


class RangedAttackAction(AttackAction):
    id: str = "ranged_attack"
    name: str = "Ranged Attack"
    description: str = ""
    action_type: ActionType = ActionType.ATTACK
    category: ActionCategory = ActionCategory.STANDARD

    @classmethod
    def from_weapon(cls, weapon: RangedWeapon) -> Self:
        return cls(
            source=weapon.name,
            description=f"Ranged Attack with {weapon.name}",
            weapon_type=weapon.weapon_type,
            targeting=weapon.targeting,
            damage_dice=weapon.damage_dice,
            damage_type=weapon.damage_type,
            stat=weapon.stat,
            range=weapon.range,
            status_effects=weapon.effects,
        )
