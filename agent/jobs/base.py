from enum import Enum

from pydantic import BaseModel, Field

from agent.character.abilities import AbilityType, SkillType
from agent.character.attributes import Proficiency
from agent.character.resources import CasterProgression
from agent.equipment.inventory import EquipmentPiece
from agent.jobs.feature import EquipmentChoice, FeatureChoice, JobFeature
from agent.jobs.spells import Spell


class JobType(str, Enum):
    BARBARIAN = "barbarian"
    CLERIC = "cleric"
    FIGHTER = "fighter"
    ROGUE = "rogue"
    WIZARD = "wizard"


class CharacterJob(BaseModel):
    """Base model for a character's archetype (Fighter, Wizard, etc.)."""

    type: JobType
    hit_die: int
    primary_ability: AbilityType
    spellcasting_ability: AbilityType | None = None
    proficiencies: list[Proficiency]
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


class JobOptions(BaseModel):
    """All selectable options for a character class."""

    job_type: JobType
    skill_choices: list[SkillType] = Field(description="Available skill proficiencies to choose from")
    skill_count: int = Field(default=2, description="Number of skills the player can select")
    equipment_choices: list[EquipmentChoice] = Field(
        default=[], description="Equipment selections available at character creation"
    )
    feature_choices: list[FeatureChoice] = Field(
        default=[], description="Class-specific feature choices (e.g., domains, fighting styles)"
    )
