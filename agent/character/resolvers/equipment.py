from collections.abc import Mapping

from pydantic import PrivateAttr, computed_field

from agent.character.resolvers.base import CharacterBase
from agent.equipment.armor import Amulet, Armor, ArmorType, Ring, Shield
from agent.equipment.base import EQUIPMENT_TYPES_PER_SLOT, EquipmentBase, EquipmentSlot, EquipmentType
from agent.equipment.weapons import UNARMED, MeleeWeapon, RangedWeapon, WeaponHandling
from agent.logs.log_event import Icon, LogLevel
from agent.logs.log_registry import get_log_registry

registry = get_log_registry()


class EquipmentResolver(CharacterBase):
    armor: Armor | None = None
    amulet: Amulet | None = None
    ring_left: Ring | None = None
    ring_right: Ring | None = None
    main_hand: MeleeWeapon | None = UNARMED
    off_hand: MeleeWeapon | Shield | None = None
    ranged: RangedWeapon | None = None

    _ring_rotation_toggle: bool = PrivateAttr(default=False)
    _two_handed_active: bool = PrivateAttr(default=False)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def armor_class(self) -> int:
        """Armor Class is derived from DEX and equipment."""
        ac = self.attributes.ac_bonus(
            armor_type=self.armor.armor_type if self.armor else None,
            max_dex_bonus=self.armor.max_dex_bonus if self.armor else None,
        )

        if self.armor:
            ac += self.armor.base_ac
        if self.off_hand and isinstance(self.off_hand, Shield):
            ac += self.off_hand.ac_bonus
        return ac

    @property
    def equipment_slots(self) -> Mapping[EquipmentSlot, EquipmentBase | None]:
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

    @property
    def two_handed_active(self) -> bool:
        return self._two_handed_active

    def _resolve_slot_for(self, item: EquipmentBase) -> EquipmentSlot | None:  # noqa: C901
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
                if self.ring_left is None:
                    slot = EquipmentSlot.RING_LEFT
                elif self.ring_right is None:
                    slot = EquipmentSlot.RING_RIGHT
                else:
                    # Both full → rotate replacement
                    self._ring_rotation_toggle = not self._ring_rotation_toggle
                    slot = EquipmentSlot.RING_LEFT if self._ring_rotation_toggle else EquipmentSlot.RING_RIGHT
            case EquipmentType.WEAPON_MELEE:
                if self.main_hand is None or self.main_hand == UNARMED:
                    slot = EquipmentSlot.MAIN_HAND
                elif self.off_hand is None:
                    slot = EquipmentSlot.OFF_HAND
            case EquipmentType.WEAPON_RANGED:
                slot = EquipmentSlot.RANGED
        return slot

    def equip(self, item: EquipmentBase, slot_name: EquipmentSlot | None = None) -> None:
        """Equip an item to a specific slot."""
        if slot_name is None:
            slot_name = self._resolve_slot_for(item)

        if not slot_name or item.type not in EQUIPMENT_TYPES_PER_SLOT[slot_name]:
            msg = f"Invalid equipment slot for {item.type.value}: {slot_name}"
            raise ValueError(msg)

        # Special case for weapons
        if isinstance(item, MeleeWeapon):
            self.equip_melee_weapon(item, slot_name)
            return

        # Standard slots (armor, shield, accessories)
        if isinstance(item, Armor) and not self.attributes.has_proficiency(item.armor_type):
            self.log_event(
                f"{self.name} is not proficient with {item.armor_type} armor and will receive some penalties.",
                log_type=LogLevel.DETAIL,
                icon=Icon.WARNING,
            )
        elif isinstance(item, Shield) and not self.attributes.has_proficiency(ArmorType.SHIELD):
            self.log_event(
                f"{self.name} is not proficient with shields and will receive some penalties.",
                log_type=LogLevel.DETAIL,
                icon=Icon.WARNING,
            )

        current: EquipmentBase = getattr(self, slot_name)
        if current:
            current.on_unequip(self)

        setattr(self, slot_name, item)
        item.on_equip(self)
        self.notify_state_change(slot_name)

    def equip_melee_weapon(self, weapon: MeleeWeapon, slot_name: EquipmentSlot) -> None:
        """
        Equip a weapon in a specific slot.
        Handles two-handed or versatile weapons with a private flag.
        """
        # Unequip existing weapon in the target slot
        current = getattr(self, slot_name.value)
        if current:
            current.on_unequip(self)
            setattr(self, slot_name.value, None)
            self.notify_state_change(slot_name.value)

        # Reset two-handed flag if equipping a new weapon
        self._two_handed_active = False

        # Handle two-handed weapons
        if weapon.handling == WeaponHandling.TWO_HANDED:
            # Only occupy main hand, leave off-hand None
            if slot_name != EquipmentSlot.MAIN_HAND:
                raise ValueError("Two-handed weapons must be equipped in main hand")
            self._two_handed_active = True
            self.off_hand = None
            self.notify_state_change("off_hand")

        # Handle versatile weapons
        if weapon.handling == WeaponHandling.VERSATILE:
            # Decide if we can use two hands
            if slot_name == EquipmentSlot.MAIN_HAND and self.off_hand is None:
                self._two_handed_active = True
            else:
                self._two_handed_active = False

        # Equip in the requested slot
        setattr(self, slot_name.value, weapon)
        weapon.on_equip(self)
        self.notify_state_change(slot_name.value)

    def unequip(self, slot_name: EquipmentSlot) -> None:
        """Unequip an item from a specific slot."""
        if slot_name not in self.equipment_slots:
            msg = f"Invalid equipment slot: {slot_name.value}"
            raise ValueError(msg)

        item = getattr(self, slot_name)
        if not item:
            return

        item.on_unequip(self)
        setattr(self, slot_name, None)
        self.notify_state_change(slot_name)

    def equip_all(self) -> None:
        """Equip all items currently assigned to slots (e.g. after load)."""
        for slot_name, item in self.equipment_slots.items():
            if not item:
                continue
            item.on_equip(self)
            self.notify_state_change(slot_name.value)
