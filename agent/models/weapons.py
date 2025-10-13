from abc import ABC

from pydantic import BaseModel

from agent.models.action import ActionCategory, ActionOption, ActionType
from agent.models.enums import DamageType, SpellLevel, StatType, TargetingType, WeaponType


class Equipment(ABC, BaseModel):
    name: str
    damage_dice: str
    damage_type: DamageType
    stat: StatType
    range: float
    description: str = ""


class Weapon(Equipment):
    name: str
    weapon_type: WeaponType
    weight: float = 0.0
    magical_bonus: int = 0

    def to_action(self, category: ActionCategory) -> ActionOption:
        return ActionOption(
            id=f"{'off_hand' if category == ActionCategory.BONUS else 'main_hand'}_attack",
            name=f"{'Off Hand' if category == ActionCategory.BONUS else 'Main Hand'} Attack",
            source=self.name,
            action_type=ActionType.MELEE_ATTACK,
            weapon_type=self.weapon_type,
            category=category,
            targeting=TargetingType.SINGLE,
            damage_dice=self.damage_dice,
            damage_type=self.damage_type,
            stat=self.stat,
            range=self.range,
        )


class MeleeWeapon(Weapon):
    stat: StatType = StatType.STR
    damage_type: DamageType = DamageType.SLASHING


class FinesseWeapon(Weapon):
    stat: StatType = StatType.DEX
    damage_type: DamageType = DamageType.PIERCING


class RangeWeapon(Weapon):
    stat: StatType = StatType.DEX
    damage_type: DamageType = DamageType.PIERCING

    def to_action(self, category: ActionCategory) -> ActionOption:
        return ActionOption(
            id="ranged_attack",
            name="Ranged Attack",
            source=self.name,
            action_type=ActionType.RANGED_ATTACK,
            weapon_type=self.weapon_type,
            category=category,
            targeting=TargetingType.SINGLE,
            damage_dice=self.damage_dice,
            damage_type=self.damage_type,
            stat=self.stat,
            range=self.range,
        )


class Spell(Equipment):
    stat: StatType = StatType.INT
    damage_type: DamageType = DamageType.MAGIC
    is_aoe: bool = False
    level: SpellLevel = SpellLevel.LEVEL_1
    casting_time: ActionCategory = ActionCategory.STANDARD

    def to_action(self) -> ActionOption:
        targeting = TargetingType.AREA if self.is_aoe else TargetingType.SINGLE
        return ActionOption(
            id=f"cast_{self.name.lower().replace(' ', '_')}",
            name=f"Cast {self.name}",
            source=self.name,
            action_type=ActionType.AOE_SPELL if targeting == TargetingType.AREA else ActionType.SPELL,
            weapon_type=WeaponType.SPELL,
            category=self.casting_time,
            targeting=targeting,
            damage_dice=self.damage_dice,
            damage_type=self.damage_type,
            stat=self.stat,
            range=self.range,
        )


class Cantrip(Spell):
    level: SpellLevel = SpellLevel.CANTRIP
