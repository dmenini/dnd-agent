from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel

from agent.effects.registry import TraitRegistry
from agent.effects.status_effects.base import StatusEffect
from agent.models.enums import FeatureId

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
    AMULET = "amulet"
    RING = "ring"
    CONSUMABLE = "consumable"
    TOOL = "tool"


class EquipmentFeature(BaseModel):
    ref_id: FeatureId
    kwargs: dict = {}


class Equipment(BaseModel):
    type: EquipmentType
    name: str
    description: str = ""
    features: list[EquipmentFeature] = []  # passive effects
    effects: list[StatusEffect] = []  # triggered effects

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
