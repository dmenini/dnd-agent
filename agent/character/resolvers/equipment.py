from typing import TYPE_CHECKING

from pydantic import computed_field

from agent.character.resolvers.base import CharacterBase
from agent.equipment.armor import Accessory, Armor, Shield
from agent.equipment.base import Equipment
from agent.equipment.weapons import UNARMED, MeleeWeapon, RangedWeapon, WeaponType
from agent.logs.log_registry import get_log_registry

if TYPE_CHECKING:
    from collections.abc import Sequence

registry = get_log_registry()


class EquipmentResolver(CharacterBase):
    proficiencies: list[WeaponType] = []

    armor: Armor | None = None
    shield: Shield | None = None
    accessories: list[Accessory] = []
    main_hand: MeleeWeapon | None = UNARMED
    off_hand: MeleeWeapon | None = None
    ranged: RangedWeapon | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def armor_class(self) -> int:
        """Armor Class is derived from DEX and equipment."""
        if self.armor:
            ac = self.attributes.ac_bonus(
                armor_type=self.armor.armor_type,
                max_dex_bonus=self.armor.max_dex_bonus,
            )
            ac += self.armor.base_ac

        else:
            ac = self.attributes.ac_bonus(armor_type=None)

        if self.shield:
            ac += self.shield.ac_bonus

        return ac

    def equip_all(self) -> None:
        # Equip to apply traits
        equipment_slots = {
            "armor": self.armor,
            "shield": self.shield,
            "accessories": self.accessories,
            "main_hand": self.main_hand,
            "off_hand": self.off_hand,
            "ranged": self.ranged,
        }

        for slot_name, item in equipment_slots.items():
            if not item:
                continue

            # Handle lists (like accessories) and single items uniformly
            items: Sequence[Equipment] = item if isinstance(item, list) else [item]  # type: ignore[list-item]
            for it in items:
                it.on_equip(self)

            self.notify_state_change(slot_name)

    def unequip(self, slot_name: str) -> None:
        equipment_slots = {
            "armor": self.armor,
            "shield": self.shield,
            "accessories": self.accessories,
            "main_hand": self.main_hand,
            "off_hand": self.off_hand,
            "ranged": self.ranged,
        }

        item = equipment_slots.get(slot_name)
        if not item:
            # Nothing equipped
            return

        items: Sequence[Equipment] = item if isinstance(item, list) else [item]  # type: ignore[list-item]
        for it in items:
            it.on_unequip(self)

        self.__setattr__(slot_name, None)
        self.notify_state_change(slot_name)
