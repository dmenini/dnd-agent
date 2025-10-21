from pydantic import BaseModel

from agent.character.stats import StatType
from agent.jobs.feature import JobFeature
from agent.jobs.spells import Spell


class CharacterJob(BaseModel):
    """Base model for a character's archetype (Fighter, Mage, etc.)."""

    name: str
    hit_die: int
    primary_stat: StatType
    save_proficiencies: list[StatType]
    features: list[JobFeature] = []
    spells: list[Spell] = []

    def get_features_for_level(self, level: int) -> list[JobFeature]:
        """Return unlocked features up to the given level."""
        return [f for f in self.features if f.level_required <= level]
