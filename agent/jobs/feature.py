from enum import Enum

from pydantic import BaseModel

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
