from pydantic import BaseModel, Field

from agent.effects.base import ModifierTrait, Trait
from agent.equipment.base import EquipmentSlot
from agent.models.enums import FeatureId


class JobFeature(BaseModel):
    """Definition of a class feature that becomes an action."""

    ref_id: FeatureId
    name: str
    description: str
    level_required: int = 1
    uses_per_rest: int | None = None
    kwargs: dict = {}


class JobPassive(BaseModel):
    """Definition of a class feature that becomes a trait."""

    trait: Trait | ModifierTrait
    level_required: int = 1


class OptionItem(BaseModel):
    id: str
    name: str
    description: str = ""


class EquipmentChoice(BaseModel):
    """Choice between equipment options."""

    slot: EquipmentSlot = Field(description="Equipment slot identifier")
    options: list[OptionItem] = Field(description="List of valid equipment choices")
    description: str = Field(description="Description of the choice")


class SubclassChoice(BaseModel):
    """Choice for a class feature (e.g., Divine Domain)."""

    feature_name: str = Field(description="Subclass name")
    options: list[OptionItem] = Field(description="Valid subclass options")
    description: str = Field(description="Description of the subclass")
    level_required: int = Field(default=1, description="Level when this choice is made")
