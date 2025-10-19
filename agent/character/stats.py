from enum import Enum

from pydantic import BaseModel

from agent.models.enums import Advantage

DEFAULT_STAT = 10
ADVANTAGE_THRESHOLD = 16
DISADVANTAGE_THRESHOLD = 8


class StatType(str, Enum):
    STR = "strength"
    DEX = "dexterity"
    CON = "constitution"
    INT = "intelligence"
    WIS = "wisdom"
    CHA = "charisma"


class Stats(BaseModel):
    strength: int = DEFAULT_STAT
    dexterity: int = DEFAULT_STAT
    constitution: int = DEFAULT_STAT
    intelligence: int = DEFAULT_STAT
    wisdom: int = DEFAULT_STAT
    charisma: int = DEFAULT_STAT

    def stat_modifier(self, stat: StatType) -> int:
        val = self.__getattribute__(stat.value)
        return (val - DEFAULT_STAT) // 2

    def stat_advantage(self, stat: StatType) -> Advantage:
        val = self.__getattribute__(stat.value)
        if val and val >= ADVANTAGE_THRESHOLD:
            return Advantage.ADVANTAGE
        if val and val <= DISADVANTAGE_THRESHOLD:
            return Advantage.DISADVANTAGE
        return Advantage.NEUTRAL
