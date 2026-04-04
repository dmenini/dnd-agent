from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field

from agent.effects.base import ModifierTrait, Trait
from agent.effects.status_effects.base import StatusEffect
from agent.models.enums import FeatureId

if TYPE_CHECKING:
    from agent.character.resolvers.base import CharacterBase
    from agent.services.trait_service import TraitService


class EquipmentSlot(str, Enum):
    AMULET = "amulet"
    ARMOR = "armor"
    RING_RIGHT = "ring_right"
    RING_LEFT = "ring_left"
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


EQUIPMENT_TYPES_PER_SLOT = {
    EquipmentSlot.AMULET: [EquipmentType.AMULET],
    EquipmentSlot.ARMOR: [EquipmentType.ARMOR],
    EquipmentSlot.RING_RIGHT: [EquipmentType.RING],
    EquipmentSlot.RING_LEFT: [EquipmentType.RING],
    EquipmentSlot.MAIN_HAND: [EquipmentType.WEAPON_MELEE],
    EquipmentSlot.OFF_HAND: [EquipmentType.WEAPON_MELEE, EquipmentType.SHIELD],
    EquipmentSlot.RANGED: [EquipmentType.WEAPON_RANGED],
}


class EquipmentFeature(BaseModel):
    # TODO: Make ref_id a str and validate the enum afterwards to not overwhelm the LLM with too many values
    ref_id: FeatureId
    trait: Trait | ModifierTrait


class EquipmentBase(BaseModel):
    type: Literal[tuple(e.value for e in EquipmentType)]  # type: ignore[valid-type]
    name: str
    description: str = ""
    rarity: Rarity = Rarity.COMMON
    features: list[EquipmentFeature] = Field(default_factory=list)
    effects: list[StatusEffect] = Field(default_factory=list)

    def on_equip(self, actor: CharacterBase) -> None:
        from agent.services.trait_service import TraitService

        for feature in self.features:
            TraitService.register_passive(actor, feature.trait)

    def on_unequip(self, actor: CharacterBase) -> None:
        from agent.services.trait_service import TraitService

        for feature in self.features:
            TraitService.unregister_passive(actor, feature_id=feature.ref_id, source_id=self.name)
