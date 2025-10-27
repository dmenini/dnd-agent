from typing import Literal

from pydantic import Field

from agent.equipment.base import EquipmentBase, EquipmentType


class Consumable(EquipmentBase):
    type: Literal[EquipmentType.CONSUMABLE] = Field(default=EquipmentType.CONSUMABLE, frozen=True)
    uses: int = 1


class Tool(EquipmentBase):
    type: Literal[EquipmentType.TOOL] = Field(default=EquipmentType.TOOL, frozen=True)
