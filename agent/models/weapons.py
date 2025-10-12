from pydantic import BaseModel

from agent.models.enums import DamageType, StatType


class Weapon(BaseModel):
    name: str
    damage_dice: str
    damage_type: DamageType
    stat: StatType
    range: float
    weight: float = 0.0
    magical_bonus: int = 0
    versatile: bool = False
    description: str = ""


class MeleeWeapon(Weapon):
    stat: StatType = StatType.STR
    damage_type: DamageType = DamageType.SLASHING


class FinesseWeapon(Weapon):
    stat: StatType = StatType.DEX
    damage_type: DamageType = DamageType.PIERCING


class RangeWeapon(Weapon):
    stat: StatType = StatType.DEX
    damage_type: DamageType = DamageType.PIERCING
    ammo: int = 20


class Spell(Weapon):
    stat: StatType = StatType.INT
    damage_type: DamageType = DamageType.MAGIC
    mana_cost: int = 5
    cooldown: int = 0
