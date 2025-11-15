from enum import Enum
from typing import Self

from pydantic import BaseModel, Field

from agent.character.abilities import AbilityType, SkillType
from agent.character.attributes import Proficiency
from agent.character.resources import CasterProgression
from agent.equipment.inventory import EquipmentPiece
from agent.jobs.feature import EquipmentChoice, JobFeature, JobPassive, SubclassChoice
from agent.jobs.spells import Spell


class JobType(str, Enum):
    BARBARIAN = "barbarian"
    CLERIC = "cleric"
    FIGHTER = "fighter"
    ROGUE = "rogue"
    WIZARD = "wizard"


class JobSpecialization(BaseModel):
    name: str
    features: list[JobFeature] = []
    passives: list[JobPassive] = []
    spells: list[Spell] = []
    proficiencies: list[Proficiency] = []


class CharacterJob(BaseModel):
    """Base model for a character's archetype (Fighter, Wizard, etc.)."""

    type: JobType
    specialization: str | None = None
    hit_die: int
    primary_ability: AbilityType
    spellcasting_ability: AbilityType | None = None
    proficiencies: list[Proficiency]
    passives: list[JobPassive] = []
    features: list[JobFeature] = []
    spells: list[Spell] = []
    spell_progression: CasterProgression
    equipment: dict[str, EquipmentPiece] = {}

    def get_features_for_level(self, level: int) -> list[JobFeature]:
        """Return unlocked features up to the given level."""
        return [f for f in self.features if f.level_required <= level]

    def get_spells_for_level(self, level: int) -> list[Spell]:
        """Return unlocked spells up to the given level."""
        return [f for f in self.spells if f.level_required <= level]

    def get_passives_for_level(self, level: int) -> list[JobPassive]:
        """Return unlocked passives up to the given level."""
        return [f for f in self.passives if f.level_required <= level]

    def apply_specialization(self, subclass: JobSpecialization) -> Self:
        """Modify this job by incorporating subclass features, spells, and proficiencies."""
        updated = self.model_copy(deep=True)
        updated.specialization = subclass.name
        updated.features += subclass.features
        updated.spells += subclass.spells
        updated.proficiencies += subclass.proficiencies
        return updated


class JobOptions(BaseModel):
    """All selectable options for a character class."""

    job_type: JobType
    skill_options: list[SkillType] = Field(description="Available skill proficiencies to choose from")
    skill_count: int = Field(default=2, description="Number of skills the player can select")
    equipment_options: list[EquipmentChoice] = Field(
        default=[], description="Equipment options available at character creation"
    )
    subclass_options: SubclassChoice = Field(description="Subclass options available for the chosen class")
