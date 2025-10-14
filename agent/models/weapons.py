from abc import ABC

from pydantic import BaseModel

from agent.actions.base import ActionCategory
from agent.models.enums import DamageType, SpellLevel, StatType, TargetingType, WeaponType


class Equipment(ABC, BaseModel):
    name: str
    damage_dice: str
    damage_type: DamageType
    targeting: TargetingType
    stat: StatType
    range: float
    description: str = ""


class Weapon(Equipment):
    name: str
    weapon_type: WeaponType
    weight: float = 0.0
    magical_bonus: int = 0


class MeleeWeapon(Weapon):
    stat: StatType = StatType.STR
    damage_type: DamageType = DamageType.SLASHING


class FinesseWeapon(Weapon):
    stat: StatType = StatType.DEX
    damage_type: DamageType = DamageType.PIERCING


class RangedWeapon(Weapon):
    stat: StatType = StatType.DEX
    damage_type: DamageType = DamageType.PIERCING


class Spell(Equipment):
    stat: StatType = StatType.INT
    damage_type: DamageType = DamageType.MAGIC
    is_aoe: bool = False
    level: SpellLevel = SpellLevel.LEVEL_1
    casting_time: ActionCategory = ActionCategory.STANDARD


class Cantrip(Spell):
    level: SpellLevel = SpellLevel.CANTRIP
