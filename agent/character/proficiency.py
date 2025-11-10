from enum import Enum

from pydantic import BaseModel

from agent.character.stats import StatType
from agent.equipment.weapons import WeaponType


class ProficiencyType(str, Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    TOOL = "tool"
    SKILL = "skill"
    SAVE = "save"


class Proficiency(BaseModel):
    type: ProficiencyType
    value: StatType | WeaponType
