from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field, computed_field

from agent.character.abilities import AbilityType
from agent.equipment.base import EquipmentBase, EquipmentType
from agent.models.constants import MELEE_RANGE
from agent.models.damage import DamageType
from agent.models.enums import TargetingType


class WeaponType(str, Enum):
    SIMPLE_MELEE = "simple_melee"
    MARTIAL_MELEE = "martial_melee"
    SIMPLE_RANGED = "simple_range"
    MARTIAL_RANGED = "martial_range"
    MAGIC = "magic"


class WeaponHandling(str, Enum):
    ONE_HANDED = "one_handed"
    TWO_HANDED = "two_handed"
    VERSATILE = "versatile"


class Weapon(EquipmentBase):
    type: Literal[EquipmentType.WEAPON_MELEE, EquipmentType.WEAPON_RANGED]
    weapon_type: WeaponType
    targeting: TargetingType = TargetingType.SINGLE
    handling: WeaponHandling = WeaponHandling.ONE_HANDED
    ability: AbilityType
    damage_dice: str
    damage_type: DamageType


class MeleeWeapon(Weapon):
    type: Literal[EquipmentType.WEAPON_MELEE] = Field(default=EquipmentType.WEAPON_MELEE, frozen=True)
    ability: AbilityType = AbilityType.STR
    reach: int = 0
    versatile_damage: str | None = None
    finesse: bool = False
    dual_wield: bool | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def range(self) -> float:
        return MELEE_RANGE + self.reach


class RangedWeapon(Weapon):
    type: Literal[EquipmentType.WEAPON_RANGED] = Field(default=EquipmentType.WEAPON_RANGED, frozen=True)
    ability: AbilityType = AbilityType.DEX
    range: float = 50
    max_range: float = 100


UNARMED = MeleeWeapon(
    name="Fists",
    description="Unarmed",
    damage_dice="1d1",
    damage_type=DamageType.BLUDGEONING,
    weapon_type=WeaponType.SIMPLE_MELEE,
)
