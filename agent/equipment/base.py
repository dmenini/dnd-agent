from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel

from agent.effects.base import StatusEffect
from agent.effects.traits import Trait

if TYPE_CHECKING:
    from agent.character.resolvers.base import CharacterBase


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
    description: str = ""
    traits: list[Trait] = []  # passive effects
    effects: list[StatusEffect] = []  # triggered effects

    def on_equip(self, character: CharacterBase) -> None:
        for trait in sorted(self.traits, key=lambda t: t.priority):
            trait.on_apply(character)

    def on_unequip(self, character: CharacterBase) -> None:
        for trait in sorted(self.traits, key=lambda t: t.priority):
            trait.on_expire(character)
