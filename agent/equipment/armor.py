from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field

from agent.equipment.base import EquipmentBase, EquipmentType


class ArmorType(str, Enum):
    SHIELD = "shield"
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"


class Armor(EquipmentBase):
    type: Literal[EquipmentType.ARMOR] = Field(default=EquipmentType.ARMOR, frozen=True)
    armor_type: ArmorType
    base_ac: int
    max_dex_bonus: int | None = None
    stealth_disadvantage: bool = False


class Shield(EquipmentBase):
    type: Literal[EquipmentType.SHIELD] = Field(default=EquipmentType.SHIELD, frozen=True)
    ac_bonus: int = 2


class Amulet(EquipmentBase):
    type: Literal[EquipmentType.AMULET] = Field(default=EquipmentType.AMULET, frozen=True)


class Ring(EquipmentBase):
    type: Literal[EquipmentType.RING] = Field(default=EquipmentType.RING, frozen=True)
