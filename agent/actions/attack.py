from typing import Self

from agent.actions.base import Action, ActionEconomy
from agent.models.enums import (
    ActionCategory,
    ActionType,
    DamageType,
    SpellLevel,
    StatType,
    TargetingType,
    WeaponType,
)
from agent.models.weapons import RangedWeapon, Spell, Weapon

ATTACK_ROLL_EXPR = "1d20"

COMBAT_ACTION_TYPES = {
    ActionType.OFF_HAND_ATTACK,
    ActionType.MAIN_HAND_ATTACK,
    ActionType.RANGED_ATTACK,
    ActionType.SPELL,
    ActionType.AOE_SPELL,
}


class AttackAction(Action):
    source: str
    targeting: TargetingType
    damage_dice: str
    damage_type: DamageType
    weapon_type: WeaponType
    stat: StatType
    range: float


class MainHandAttackAction(AttackAction):
    id: str = "main_hand_attack"
    name: str = "Main Hand Attack"
    description: str = "Base attack with main hand weapon."
    action_type: ActionType = ActionType.MAIN_HAND_ATTACK
    category: ActionCategory = ActionCategory.STANDARD

    @classmethod
    def from_weapon(cls, weapon: Weapon) -> Self:
        return cls(
            source=weapon.name,
            weapon_type=weapon.weapon_type,
            targeting=weapon.targeting,
            damage_dice=weapon.damage_dice,
            damage_type=weapon.damage_type,
            stat=weapon.stat,
            range=weapon.range,
        )


class OffHandAttackAction(AttackAction):
    id: str = "off_hand_attack"
    name: str = "Off Hand Attack"
    description: str = "Bonus attack with off hand weapon."
    action_type: ActionType = ActionType.OFF_HAND_ATTACK
    category: ActionCategory = ActionCategory.BONUS

    @classmethod
    def from_weapon(cls, weapon: Weapon) -> Self:
        return cls(
            source=weapon.name,
            weapon_type=weapon.weapon_type,
            targeting=weapon.targeting,
            damage_dice=weapon.damage_dice,
            damage_type=weapon.damage_type,
            stat=weapon.stat,
            range=weapon.range,
        )

    def is_available(self, action_economy: ActionEconomy) -> bool:
        raise action_economy.bonus_actions > 0


class RangedAttackAction(AttackAction):
    id: str = "ranged_attack"
    name: str = "Ranged Attack"
    description: str = "Base attack with ranged weapon."
    action_type: ActionType = ActionType.RANGED_ATTACK
    category: ActionCategory = ActionCategory.STANDARD

    @classmethod
    def from_weapon(cls, weapon: RangedWeapon) -> Self:
        return cls(
            source=weapon.name,
            weapon_type=weapon.weapon_type,
            targeting=weapon.targeting,
            damage_dice=weapon.damage_dice,
            damage_type=weapon.damage_type,
            stat=weapon.stat,
            range=weapon.range,
        )


class SpellAction(AttackAction):
    id: str = "cast_spell"
    name: str = "Cast Spell"
    description: str = "Cast spell."
    action_type: ActionType = ActionType.SPELL
    category: ActionCategory = ActionCategory.STANDARD
    level: SpellLevel

    @classmethod
    def from_spell(cls, spell: Spell) -> Self:
        return cls(
            id=f"cast_{spell.name.lower().replace(' ', '_')}",
            name=f"Cast {spell.name}",
            description=spell.description,
            source=spell.name,
            action_type=ActionType.AOE_SPELL if spell.targeting == TargetingType.AREA else ActionType.SPELL,
            weapon_type=WeaponType.SPELL,
            category=spell.casting_time,
            targeting=spell.targeting,
            damage_dice=spell.damage_dice,
            damage_type=spell.damage_type,
            stat=spell.stat,
            range=spell.range,
            level=spell.level,
        )
