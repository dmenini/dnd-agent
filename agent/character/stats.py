from enum import Enum

from pydantic import BaseModel

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

    def modifier(self, stat: StatType) -> int:
        val = self.__getattribute__(stat.value)
        return (val - DEFAULT_STAT) // 2

    def advantage(self, stat: StatType) -> bool | None:
        val = self.__getattribute__(stat.value)
        if val and val >= ADVANTAGE_THRESHOLD:
            return True
        if val and val <= DISADVANTAGE_THRESHOLD:
            return False
        return None


class Attributes(BaseModel):
    base_hp: int = 8
    base_ac: int = 2
    base_speed: float = 6.0
    vision_range: float = 10.0

    # dynamic fields updated during play
    current_hp: int = 8
    current_movement: float = 6.0

    def compute_max_hp(self, level: int, stats: Stats) -> int:
        """HP grows with level and Constitution modifier."""
        return self.base_hp + (level - 1) * (5 + stats.modifier(StatType.CON))

    def compute_ac(self, stats: Stats, dex_cap: int | None = None) -> int:
        """Base AC + DEX modifier (possibly capped by armor)."""
        dex_mod = stats.modifier(StatType.DEX)
        if dex_cap is not None:
            dex_mod = min(dex_mod, dex_cap)
        return self.base_ac + dex_mod

    def compute_initiative(self, stats: Stats) -> int:
        """Derived initiative bonus."""
        return stats.modifier(StatType.DEX)

    def compute_speed(self, stats: Stats) -> float:  # noqa: ARG002
        """Base speed, possibly affected by conditions later."""
        return self.base_speed
