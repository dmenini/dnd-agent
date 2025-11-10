from enum import Enum

from pydantic import BaseModel

from agent.character.abilities import AbilityType, SkillType
from agent.equipment.armor import ArmorType
from agent.equipment.weapons import WeaponType


class ProficiencyType(str, Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    TOOL = "tool"
    SKILL = "skill"
    SAVE = "save"


type ProficiencyTarget = AbilityType | WeaponType | ArmorType | SkillType


class Proficiency(BaseModel):
    type: ProficiencyType
    target: ProficiencyTarget

    def __str__(self) -> str:
        return f"{self.target.title()} ({self.type.title()})"
