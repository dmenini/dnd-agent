from enum import Enum

from pydantic import BaseModel

from agent.character.stats import StatType
from agent.equipment.weapons import WeaponType
from agent.jobs.feature import JobFeature
from agent.jobs.spells import Spell


class JobType(str, Enum):
    BARBARIAN = "barbarian"
    CLERIC = "cleric"
    FIGHTER = "fighter"
    WIZARD = "wizard"


class CharacterJob(BaseModel):
    """Base model for a character's archetype (Fighter, Mage, etc.)."""

    type: JobType
    hit_die: int
    primary_stat: StatType
    save_proficiencies: list[StatType]
    weapon_proficiencies: list[WeaponType]
    features: list[JobFeature] = []
    spells: list[Spell] = []

    def get_features_for_level(self, level: int) -> list[JobFeature]:
        """Return unlocked features up to the given level."""
        return [f for f in self.features if f.level_required <= level]

    def get_spells_for_level(self, level: int) -> list[Spell]:
        """Return unlocked spells up to the given level."""
        return [f for f in self.spells if f.level_required <= level]
