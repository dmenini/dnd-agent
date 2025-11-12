from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel

from agent.effects.registry import TraitRegistry
from agent.effects.status_effects.base import StatusEffect
from agent.models.enums import FeatureId

if TYPE_CHECKING:
    from agent.character.resolvers.base import CharacterBase


class EquipmentSlot(str, Enum):
    AMULET = "amulet"
    ARMOR = "armor"
    RING_RIGHT = "ring_right"
    RING_LEFT = "ring_left"
    SHIELD = "shield"
    MAIN_HAND = "main_hand"
    OFF_HAND = "off_hand"
    RANGED = "ranged"


class Rarity(str, Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    VERY_RARE = "very_rare"
    LEGENDARY = "legendary"


class EquipmentType(str, Enum):
    AMULET = "amulet"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    RING = "ring"
    SHIELD = "shield"
    TOOL = "tool"
    WEAPON_MELEE = "weapon_melee"
    WEAPON_RANGED = "weapon_ranged"


class EquipmentFeature(BaseModel):
    ref_id: FeatureId
    kwargs: dict = {}


class EquipmentBase(BaseModel):
    type: Literal[tuple(e.value for e in EquipmentType)]  # type: ignore[valid-type]
    name: str
    description: str = ""
    rarity: Rarity = Rarity.COMMON
    features: list[EquipmentFeature] = []
    effects: list[StatusEffect] = []

    def on_equip(self, actor: CharacterBase) -> None:
        for feature in self.features:
            trait = TraitRegistry.create(
                feature_id=feature.ref_id,
                source_id=self.name,
                **feature.kwargs,
            )
            actor.register_passive(trait=trait)

    def on_unequip(self, actor: CharacterBase) -> None:
        for feature in self.features:
            actor.unregister_passive(feature_id=feature.ref_id, source_id=self.name)
