from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel

from agent.character.stats import StatType
from agent.effects.base import StatusEffect
from agent.effects.traits import Trait

if TYPE_CHECKING:
    from agent.character.character import Character


class Rarity(str, Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    VERY_RARE = "very_rare"
    LEGENDARY = "legendary"


class EquipmentType(str, Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    SHIELD = "shield"
    ACCESSORY = "accessory"
    CONSUMABLE = "consumable"
    TOOL = "tool"


class Equipment(BaseModel):
    name: str
    stat: StatType
    range: float
    description: str = ""
    traits: list[Trait] = []  # passive effects
    effects: list[StatusEffect] = []  # triggered effects

    def on_equip(self, character: Character) -> None:
        for trait in self.traits:
            if hasattr(trait, "on_apply"):
                trait.on_apply(character)

    def on_unequip(self, character: Character) -> None:
        for trait in self.traits:
            if hasattr(trait, "on_expire"):
                trait.on_expire(character)
