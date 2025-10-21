from pydantic import computed_field

from agent.character.resolvers.base import CharacterBase
from agent.equipment.armor import Accessory, Armor, Shield
from agent.equipment.weapons import UNARMED, MeleeWeapon, RangedWeapon, WeaponType
from agent.logs.log_registry import get_log_registry

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
        if self.armor:
            self.armor.on_equip(self)
        if self.shield:
            self.shield.on_equip(self)
        if self.accessories:
            for acc in self.accessories:
                acc.on_equip(self)
        if self.main_hand:
            self.main_hand.on_equip(self)
        if self.off_hand:
            self.off_hand.on_equip(self)
        if self.ranged:
            self.ranged.on_equip(self)
