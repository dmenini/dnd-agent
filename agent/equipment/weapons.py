from __future__ import annotations

from enum import Enum

from pydantic import Field, computed_field

from agent.character.stats import StatType
from agent.equipment.base import Equipment, EquipmentType
from agent.models.constants import MELEE_RANGE
from agent.models.damage import DamageType
from agent.models.enums import TargetingType


class WeaponType(str, Enum):
    SIMPLE_MELEE = "simple_melee"
    MARTIAL_MELEE = "martial_melee"
    SIMPLE_RANGE = "simple_range"
    MARTIAL_RANGE = "martial_range"
    MAGIC = "magic"


class WeaponHandling(str, Enum):
    ONE_HANDED = "one_handed"
    TWO_HANDED = "two_handed"
    VERSATILE = "versatile"


class Weapon(Equipment):
    type: EquipmentType = Field(default=EquipmentType.WEAPON, frozen=True)
    weapon_type: WeaponType
    targeting: TargetingType = TargetingType.SINGLE
    handling: WeaponHandling = WeaponHandling.ONE_HANDED
    stat: StatType
    damage_dice: str
    damage_type: DamageType


class MeleeWeapon(Weapon):
    stat: StatType = StatType.STR
    reach: int = 0
    versatile_damage: str | None = None
    finesse: bool = False
    dual_wield: bool | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def range(self) -> float:
        return MELEE_RANGE + self.reach


class RangedWeapon(Weapon):
    stat: StatType = StatType.DEX
    ammo_type: str | None = None
    range: float = 50
    max_range: float = 100


UNARMED = MeleeWeapon(
    name="Fists",
    description="Unarmed",
    damage_dice="1d1",
    damage_type=DamageType.BLUDGEONING,
    weapon_type=WeaponType.SIMPLE_MELEE,
)
