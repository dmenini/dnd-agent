from agent.character.stats import StatType
from agent.equipment.base import Equipment
from agent.models.enums import DamageType, WeaponType


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
