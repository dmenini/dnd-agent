from pydantic import Field

from agent.equipment.base import Equipment, EquipmentType


class Consumable(Equipment):
    type: EquipmentType = Field(default=EquipmentType.CONSUMABLE, frozen=True)
    uses: int = 1


class Tool(Equipment):
    type: EquipmentType = Field(default=EquipmentType.TOOL, frozen=True)
