from enum import Enum

from pydantic import BaseModel, Field

from agent.equipment.base import EquipmentSlot
from agent.models.enums import FeatureId


class FeatureType(str, Enum):
    PASSIVE = "passive"  # trait
    ACTIVE = "active"  # action
    SPELL = "spell"


class JobFeature(BaseModel):
    """Definition of a class feature that becomes a trait or action."""

    ref_id: FeatureId
    name: str
    description: str
    type: FeatureType
    level_required: int = 1
    uses_per_rest: int | None = None
    kwargs: dict = {}


class EquipmentChoice(BaseModel):
    """Choice between equipment options."""

    slot: EquipmentSlot = Field(description="Equipment slot identifier")
    options: list[str] = Field(description="List of valid equipment choices")
    description: str = Field(description="Description of the choice")


class FeatureChoice(BaseModel):
    """Choice for a class feature (e.g., Divine Domain)."""

    feature_name: str = Field(description="Name of the feature being chosen")
    options: list[str] = Field(description="Valid options for this feature")
    description: str = Field(description="What this feature represents")
    level_required: int = Field(default=1, description="Level when this choice is made")
