from enum import Enum

from pydantic import BaseModel, Field

from agent.character.stats import StatType


class FeatureType(str, Enum):
    PASSIVE = "passive"  # trait
    ACTIVE = "active"  # action


class JobFeature(BaseModel):
    """Declarative definition of a class feature that becomes a trait or action."""

    name: str
    description: str
    level_required: int
    type: FeatureType
    reference_id: str
    uses_per_rest: int | None = None


class CharacterJob(BaseModel):
    """Base model for a character's archetype (Fighter, Mage, etc.)."""

    name: str
    hit_die: int
    primary_stat: StatType
    save_proficiencies: list[StatType]
    features: list[JobFeature] = Field(default_factory=list)

    def get_features_for_level(self, level: int) -> list[JobFeature]:
        """Return unlocked features up to the given level."""
        return [f for f in self.features if f.level_required <= level]
