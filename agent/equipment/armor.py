from __future__ import annotations

from enum import Enum

from pydantic import Field

from agent.equipment.base import Equipment, EquipmentType


class ArmorType(str, Enum):
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"


class Armor(Equipment):
    type: EquipmentType = Field(default=EquipmentType.ARMOR, frozen=True)
    armor_type: ArmorType
    base_ac: int
    max_dex_bonus: int | None = None
    stealth_disadvantage: bool = False


class Shield(Equipment):
    type: EquipmentType = Field(default=EquipmentType.SHIELD, frozen=True)


class Amulet(Equipment):
    type: EquipmentType = Field(default=EquipmentType.AMULET, frozen=True)


class Ring(Equipment):
    type: EquipmentType = Field(default=EquipmentType.RING, frozen=True)
