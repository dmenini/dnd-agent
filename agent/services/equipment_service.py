"""Service for managing character equipment."""

from typing import TYPE_CHECKING

from agent.equipment.armor import Armor, ArmorType, Shield
from agent.equipment.base import EQUIPMENT_TYPES_PER_SLOT, EquipmentBase, EquipmentSlot, EquipmentType
from agent.equipment.weapons import UNARMED, MeleeWeapon, WeaponHandling
from agent.logs.log_event import Icon, LogLevel
from agent.services.trait_service import TraitService

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.character.equipment import Equipment


class EquipmentService:
    """Stateless service for equipment management."""

    @classmethod
    def _resolve_slot_for(cls, equipment: "Equipment", item: EquipmentBase) -> EquipmentSlot | None:  # noqa: C901
        """Automatically determine which slot an equipment item should occupy."""

        slot: EquipmentSlot | None = None
        match item.type:
            case EquipmentType.ARMOR:
                slot = EquipmentSlot.ARMOR
            case EquipmentType.SHIELD:
                slot = EquipmentSlot.OFF_HAND
            case EquipmentType.AMULET:
                slot = EquipmentSlot.AMULET
            case EquipmentType.RING:
                # Prioritize empty ring slots
                if equipment.ring_left is None:
                    slot = EquipmentSlot.RING_LEFT
                elif equipment.ring_right is None:
                    slot = EquipmentSlot.RING_RIGHT
                else:
                    # Both full → rotate replacement
                    equipment.ring_rotation_toggle = not equipment.ring_rotation_toggle
                    slot = EquipmentSlot.RING_LEFT if equipment.ring_rotation_toggle else EquipmentSlot.RING_RIGHT
            case EquipmentType.WEAPON_MELEE:
                if equipment.main_hand is None or equipment.main_hand == UNARMED:
                    slot = EquipmentSlot.MAIN_HAND
                elif equipment.off_hand is None:
                    slot = EquipmentSlot.OFF_HAND
            case EquipmentType.WEAPON_RANGED:
                slot = EquipmentSlot.RANGED
        return slot

    @classmethod
    def equip(cls, character: "Character", item: EquipmentBase, slot_name: EquipmentSlot | None = None) -> None:
        """Equip an item to a specific slot."""
        if slot_name is None:
            slot_name = cls._resolve_slot_for(character.equipment, item)

        if not slot_name or item.type not in EQUIPMENT_TYPES_PER_SLOT[slot_name]:
            msg = f"Invalid equipment slot for {item.type.value}: {slot_name}"
            raise ValueError(msg)

        # Special case for weapons
        if isinstance(item, MeleeWeapon):
            cls.equip_melee_weapon(character, item, slot_name)
            return

        # Standard slots (armor, shield, accessories)
        if isinstance(item, Armor) and not character.attributes.has_proficiency(item.armor_type):
            character.log_event(
                f"{character.name} is not proficient with {item.armor_type} armor and will receive some penalties.",
                log_type=LogLevel.DETAIL,
                icon=Icon.WARNING,
            )
        elif isinstance(item, Shield) and not character.attributes.has_proficiency(ArmorType.SHIELD):
            character.log_event(
                f"{character.name} is not proficient with shields and will receive some penalties.",
                log_type=LogLevel.DETAIL,
                icon=Icon.WARNING,
            )

        current: EquipmentBase = getattr(character.equipment, slot_name)
        if current:
            current.on_unequip(character)

        setattr(character.equipment, slot_name, item)
        item.on_equip(character)
        TraitService.notify_state_change(character, f"equipment.{slot_name.value}")

    @classmethod
    def equip_melee_weapon(cls, character: "Character", weapon: MeleeWeapon, slot_name: EquipmentSlot) -> None:
        """
        Equip a weapon in a specific slot.
        Handles two-handed or versatile weapons with a private flag.
        """
        equipment = character.equipment

        # Unequip existing weapon in the target slot
        current = getattr(equipment, slot_name.value)
        if current:
            current.on_unequip(character)
            setattr(equipment, slot_name.value, None)
            TraitService.notify_state_change(character, f"equipment.{slot_name.value}")

        # Reset two-handed flag if equipping a new weapon
        equipment.two_handed_active = False

        # Handle two-handed weapons
        if weapon.handling == WeaponHandling.TWO_HANDED:
            # Only occupy main hand, leave off-hand None
            if slot_name != EquipmentSlot.MAIN_HAND:
                raise ValueError("Two-handed weapons must be equipped in main hand")
            equipment.two_handed_active = True
            equipment.off_hand = None
            TraitService.notify_state_change(character, "equipment.off_hand")

        # Handle versatile weapons
        if weapon.handling == WeaponHandling.VERSATILE:
            # Decide if we can use two hands
            if slot_name == EquipmentSlot.MAIN_HAND and equipment.off_hand is None:
                equipment.two_handed_active = True
            else:
                equipment.two_handed_active = False

        # Equip in the requested slot
        setattr(equipment, slot_name.value, weapon)
        weapon.on_equip(character)
        TraitService.notify_state_change(character, f"equipment.{slot_name.value}")

    @classmethod
    def unequip(cls, character: "Character", slot_name: EquipmentSlot) -> None:
        """Unequip an item from a specific slot."""
        equipment = character.equipment

        if slot_name not in equipment.slots:
            msg = f"Invalid equipment slot: {slot_name.value}"
            raise ValueError(msg)

        item = getattr(equipment, slot_name)
        if not item:
            return

        item.on_unequip(character)
        setattr(equipment, slot_name, None)
        TraitService.notify_state_change(character, f"equipment.{slot_name.value}")

    @classmethod
    def equip_all(cls, character: "Character") -> None:
        """Equip all items currently assigned to slots (e.g. after load)."""
        equipment = character.equipment

        for slot_name, item in equipment.slots.items():
            if not item:
                continue
            item.on_equip(character)
            TraitService.notify_state_change(character, f"equipment.{slot_name.value}")
