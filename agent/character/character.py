from typing import Any

from pydantic import BaseModel

from agent.character.abilities import Abilities
from agent.character.resolvers.base import CharacterBase
from agent.services.equipment_service import EquipmentService
from agent.services.job_service import JobService
from agent.services.trait_service import TraitService


class Party(BaseModel):
    id: str
    name: str
    is_player_party: bool = False


class Character(CharacterBase):
    party: Party

    def model_post_init(self, _: Any, /) -> None:
        """Hook running after every initialization (also after deserialization)."""
        # Make sure that passives are synced
        for passive in self.passives:
            TraitService.register_passive(self, passive)

        # HP set to -1 means that it's the first initialization
        if self.attributes.hp == -1:
            EquipmentService.equip_all(self)
            JobService.apply_job_features(self)
            self.attributes.hp = self.max_hp

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
