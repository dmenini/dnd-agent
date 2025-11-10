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


class Proficiency(BaseModel):
    type: ProficiencyType
    value: AbilityType | WeaponType | ArmorType | SkillType
