from abc import ABC

from pydantic import BaseModel

from agent.actions.base import ActionCategory
from agent.effects.base import StatusEffect
from agent.models.enums import DamageType, SpellLevel, StatType, TargetingType, WeaponType


class Equipment(ABC, BaseModel):
    name: str
    targeting: TargetingType
    stat: StatType
    range: float
    description: str = ""
    status_effects: list[StatusEffect] = []


class Weapon(Equipment):
    name: str
    damage_dice: str
    damage_type: DamageType
    weapon_type: WeaponType
    weight: float = 0.0


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
    is_aoe: bool = False
    level: SpellLevel = SpellLevel.LEVEL_1
    casting_time: ActionCategory = ActionCategory.STANDARD


class AttackSpell(Spell):
    stat: StatType = StatType.INT
    damage_dice: str
    damage_type: DamageType = DamageType.MAGIC


class SupportSpell(Spell):
    stat: StatType = StatType.WIS
