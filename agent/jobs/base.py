from collections.abc import Callable
from enum import Enum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field

from agent.actions.composable import ComposableAction
from agent.character.abilities import AbilityType, SkillType
from agent.character.attributes import Proficiency
from agent.character.resources import CasterProgression
from agent.equipment.inventory import EquipmentPiece
from agent.jobs.feature import EquipmentChoice, JobFeature, JobPassive, SubclassChoice


class JobType(str, Enum):
    BARBARIAN = "barbarian"
    CLERIC = "cleric"
    FIGHTER = "fighter"
    ROGUE = "rogue"
    WIZARD = "wizard"


class ResourceDefinition(BaseModel):
    """Defines a limited-use resource for a character class (Channel Divinity, Ki, Rage, etc.)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    calculate_max_uses: Callable[[int], int] = Field(default=lambda _: 1, exclude=True)
    restore_on_short_rest: bool = False
    restore_on_long_rest: bool = True


class JobSpecialization(BaseModel):
    name: str
    features: list[JobFeature] = Field(default_factory=list)
    passives: list[JobPassive] = Field(default_factory=list)
    spells: list[ComposableAction] = Field(default_factory=list)
    proficiencies: list[Proficiency] = Field(default_factory=list)
    resources: list[ResourceDefinition] = Field(default_factory=list)


class CharacterJob(BaseModel):
    """Base model for a character's archetype (Fighter, Wizard, etc.)."""

    type: JobType
    specialization: str | None = None
    hit_die: int
    primary_ability: AbilityType
    spellcasting_ability: AbilityType | None = None
    proficiencies: list[Proficiency]
    passives: list[JobPassive] = Field(default_factory=list)
    features: list[JobFeature] = Field(default_factory=list)
    spells: list[ComposableAction] = Field(default_factory=list)
    spell_progression: CasterProgression
    equipment: dict[str, EquipmentPiece] = Field(default_factory=dict)
    resources: list[ResourceDefinition] = Field(default_factory=list)

    def get_features_for_level(self, level: int) -> list[JobFeature]:
        """Return unlocked features up to the given level."""
        return [f for f in self.features if f.level_required <= level]

    def get_spells_for_level(self, level: int) -> list[ComposableAction]:
        """Return unlocked spells up to the given level.

        Spells use level_required for level gating (defaults to 1 if None).
        """
        return [spell for spell in self.spells if (spell.level_required or 1) <= level]

    def get_passives_for_level(self, level: int) -> list[JobPassive]:
        """Return unlocked passives up to the given level."""
        return [f for f in self.passives if f.level_required <= level]

    def apply_specialization(self, subclass: JobSpecialization) -> Self:
        """Modify this job by incorporating subclass features, spells, proficiencies, and resources."""
        updated = self.model_copy(deep=True)
        updated.specialization = subclass.name
        updated.features += subclass.features
        updated.passives += subclass.passives
        updated.spells += subclass.spells
        updated.proficiencies += subclass.proficiencies
        updated.resources += subclass.resources
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
