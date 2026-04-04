from typing import Any

from pydantic import BaseModel, computed_field

from agent.character.abilities import Abilities
from agent.character.resolvers.job import JobResolver
from agent.equipment.armor import Shield
from agent.services.equipment_service import EquipmentService


class Party(BaseModel):
    id: str
    name: str
    is_player_party: bool = False


class Character(JobResolver):
    party: Party

    def model_post_init(self, _: Any, /) -> None:
        """Hook running after every initialization (also after deserialization)."""
        # Make sure that passives are synced
        for passive in self.passives:
            self.register_passive(passive)

        # HP set to -1 means that it's the first initialization
        if self.attributes.hp == -1:
            EquipmentService.equip_all(self)
            self.apply_job_features()
            self.attributes.hp = self.max_hp

    @computed_field  # type: ignore[prop-decorator]
    @property
    def current_speed(self) -> float:
        return self.attributes.speed() - self.combat.action_economy.movement_used

    @computed_field  # type: ignore[prop-decorator]
    @property
    def initiative_modifier(self) -> int:
        return self.attributes.initiative()

    # Backward compatibility property for turn_done
    @property
    def turn_done(self) -> bool:
        return self.combat.turn_done

    @turn_done.setter
    def turn_done(self, value: bool) -> None:
        self.combat.turn_done = value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def armor_class(self) -> int:
        """Armor Class is derived from DEX and equipment."""
        ac = self.attributes.ac_bonus(
            armor_type=self.equipment.armor.armor_type if self.equipment.armor else None,
            max_dex_bonus=self.equipment.armor.max_dex_bonus if self.equipment.armor else None,
        )

        if self.equipment.armor:
            ac += self.equipment.armor.base_ac
        if self.equipment.off_hand and isinstance(self.equipment.off_hand, Shield):
            ac += self.equipment.off_hand.ac_bonus
        return ac

    def __str__(self) -> str:
        return (
            f"**{self.name} {self.icon} (ID: {self.id})**\n\n"
            f"Class: {self.job.type.value} | Level: {self.level} | Party: {self.party.name}\n\n"
            f"HP: {self.attributes.hp}/{self.max_hp} | AC: {self.armor_class}\n\n"
            f"Position: ({self.pos.x}, {self.pos.y}) | Facing: {self.pos.direction} | "
            f"Movement Remaining: {self.current_speed}/{self.speed} steps | Hidden: {self.is_hidden}\n\n"
            f"Status Effects: {', '.join(str(eff) for eff in self.status_effects) or 'None'}\n\n"
            f"Passives: {', '.join(eff.name for eff in self.passives) or 'None'}\n\n"
            f"Spell Slots: {self.spell_slots}\n\n"
            f"Abilities: {Abilities.model_validate(self.attributes.model_dump())}"
        )
