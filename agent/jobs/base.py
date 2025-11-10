from enum import Enum

from pydantic import BaseModel

from agent.character.abilities import AbilityType
from agent.character.attributes import Proficiency
from agent.jobs.feature import JobFeature
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
    proficiencies: list[Proficiency]
    features: list[JobFeature] = []
    spells: list[Spell] = []

    def get_features_for_level(self, level: int) -> list[JobFeature]:
        """Return unlocked features up to the given level."""
        return [f for f in self.features if f.level_required <= level]

    def get_spells_for_level(self, level: int) -> list[Spell]:
        """Return unlocked spells up to the given level."""
        return [f for f in self.spells if f.level_required <= level]
