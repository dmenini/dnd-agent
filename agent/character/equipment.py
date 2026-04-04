"""Character equipment data model."""

from collections.abc import Mapping

from pydantic import BaseModel

from agent.equipment.armor import Amulet, Armor, Ring, Shield
from agent.equipment.base import EquipmentBase, EquipmentSlot
from agent.equipment.weapons import UNARMED, MeleeWeapon, RangedWeapon


class Equipment(BaseModel):
    """All equipped items."""

    armor: Armor | None = None
    amulet: Amulet | None = None
    ring_left: Ring | None = None
    ring_right: Ring | None = None
    main_hand: MeleeWeapon | None = UNARMED
    off_hand: MeleeWeapon | Shield | None = None
    ranged: RangedWeapon | None = None

    # Internal state
    ring_rotation_toggle: bool = False
    two_handed_active: bool = False

    @property
    def slots(self) -> Mapping[EquipmentSlot, EquipmentBase | None]:
        """Mapping of slot names to currently equipped items."""
        return {
            EquipmentSlot.ARMOR: self.armor,
            EquipmentSlot.AMULET: self.amulet,
            EquipmentSlot.RING_LEFT: self.ring_left,
            EquipmentSlot.RING_RIGHT: self.ring_right,
            EquipmentSlot.MAIN_HAND: self.main_hand,
            EquipmentSlot.OFF_HAND: self.off_hand,
            EquipmentSlot.RANGED: self.ranged,
        }
