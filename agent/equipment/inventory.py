from typing import Annotated

from pydantic import BaseModel, Field

from agent.equipment.armor import Amulet, Armor, Ring, Shield
from agent.equipment.consumable import Consumable, Tool
from agent.equipment.weapons import MeleeWeapon, RangedWeapon

type EquipmentPiece = Annotated[
    Armor | Shield | Amulet | Ring | MeleeWeapon | RangedWeapon | Tool | Consumable,
    Field(discriminator="type"),
]


class Inventory(BaseModel):
    equipment: list[EquipmentPiece]
    capacity: int | None = None
    gold: int = 0
    weight: float = 0.0
    equipped_items: dict[str, EquipmentPiece] = {}
