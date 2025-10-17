from enum import Enum

from pydantic import Field

from agent.character.stats import StatType
from agent.equipment.base import Equipment, EquipmentType
from agent.models.damage import DamageType
from agent.models.enums import TargetingType


class WeaponType(str, Enum):
    SIMPLE_MELEE = "simple_melee"
    MARTIAL_MELEE = "martial_melee"
    SIMPLE_RANGE = "simple_range"
    MARTIAL_RANGE = "martial_range"
    MAGIC = "magic"


class Weapon(Equipment):
    type: EquipmentType = Field(default=EquipmentType.WEAPON, frozen=True)
    weapon_type: WeaponType
    stat: StatType
    damage_dice: str
    damage_type: DamageType
    range: float = 5
    targeting: TargetingType = TargetingType.SINGLE


class MeleeWeapon(Weapon):
    stat: StatType = StatType.STR


class RangedWeapon(Weapon):
    stat: StatType = StatType.DEX
    ammo_type: str | None = None
    range: float = 10


UNARMED = MeleeWeapon(
    name="Fists",
    description="Unarmed",
    damage_dice="1d1",
    damage_type=DamageType.BLUDGEONING,
    weapon_type=WeaponType.SIMPLE_MELEE,
)
