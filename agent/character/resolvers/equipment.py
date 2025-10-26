from collections.abc import Mapping

from pydantic import PrivateAttr, computed_field

from agent.character.resolvers.base import CharacterBase
from agent.equipment.armor import Amulet, Armor, Shield
from agent.equipment.base import Equipment, EquipmentType
from agent.equipment.weapons import UNARMED, MeleeWeapon, RangedWeapon, WeaponType
from agent.logs.log_registry import get_log_registry

registry = get_log_registry()


class EquipmentResolver(CharacterBase):
    proficiencies: list[WeaponType] = []

    armor: Armor | None = None
    shield: Shield | None = None
    amulet: Amulet | None = None
    ring_left: Amulet | None = None
    ring_right: Amulet | None = None
    main_hand: MeleeWeapon | None = UNARMED
    off_hand: MeleeWeapon | None = None
    ranged: RangedWeapon | None = None

    _ring_rotation_toggle = PrivateAttr(default=False)  # track which ring to replace next

    @property
    def equipment_slots(self) -> Mapping[str, Equipment | None]:
        """Mapping of slot names to currently equipped items."""
        return {
            "armor": self.armor,
            "shield": self.shield,
            "amulet": self.amulet,
            "ring_left": self.ring_left,
            "ring_right": self.ring_right,
            "main_hand": self.main_hand,
            "off_hand": self.off_hand,
            "ranged": self.ranged,
        }

    def _resolve_slot_for(self, item: Equipment) -> str | None:
        """Automatically determine which slot an equipment item should occupy."""
        slot: str | None = None
        match item.type:
            case EquipmentType.ARMOR:
                slot = "armor"
            case EquipmentType.SHIELD:
                slot = "shield"
            case EquipmentType.AMULET:
                slot = "amulet"
            case EquipmentType.RING:
                # Prioritize empty ring slots
                if self.ring_left is None:
                    slot = "ring_left"
                elif self.ring_right is None:
                    slot = "ring_right"
                else:
                    # Both full → rotate replacement
                    self._ring_rotation_toggle = not self._ring_rotation_toggle
                    slot = "ring_left" if self._ring_rotation_toggle else "ring_right"
            case EquipmentType.WEAPON:
                if self.main_hand is None or self.main_hand == UNARMED:
                    slot = "main_hand"
                elif self.off_hand is None:
                    slot = "off_hand"
                else:
                    slot = "ranged" if isinstance(item, RangedWeapon) else None
        return slot

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
        if self.shield:
            ac += self.shield.ac_bonus
        return ac

    def equip(self, item: Equipment, slot_name: str | None = None) -> None:
        """Equip an item to a specific slot."""
        if slot_name is None:
            slot_name = self._resolve_slot_for(item)

        if not slot_name or slot_name not in self.equipment_slots:
            msg = f"Invalid equipment slot: {slot_name}"
            raise ValueError(msg)

        current: Equipment = getattr(self, slot_name)
        if current:
            current.on_unequip(self)

        setattr(self, slot_name, item)
        item.on_equip(self)
        self.notify_state_change(slot_name)

    def unequip(self, slot_name: str) -> None:
        """Unequip an item from a specific slot."""
        if slot_name not in self.equipment_slots:
            msg = f"Invalid equipment slot: {slot_name}"
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
            self.notify_state_change(slot_name)
