from collections import defaultdict
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, PrivateAttr

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


class Modifier(BaseModel):
    source_id: str
    attribute: str
    value: Any
    operation: Literal["set", "add", "mul"] = "set"


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

    def advantage(self, stat: StatType) -> int:
        val = self.__getattribute__(stat.value)
        if val and val >= ADVANTAGE_THRESHOLD:
            return 1
        if val and val <= DISADVANTAGE_THRESHOLD:
            return -1
        return 0


class Attributes(BaseModel):
    base_hp: int = 8
    base_ac: int = 2
    base_speed: float = 6.0
    base_vision_range: float = 10.0
    base_attack_advantage: int = 0
    base_defense_advantage: int = 0
    base_dex_save_advantage: int = 0
    base_wis_save_advantage: int = 0
    base_autocrit: bool = False

    hp: int = 8

    _modifiers: dict[str, list[Modifier]] = PrivateAttr(default_factory=lambda: defaultdict(list))

    def compute_max_hp(self, level: int, stats: Stats) -> int:
        """HP grows with level and Constitution modifier."""
        return self.base_hp + (level - 1) * (5 + stats.modifier(StatType.CON))

    def compute_ac(self, stats: Stats, dex_cap: int | None = None) -> int:
        """Base AC + DEX modifier (possibly capped by armor)."""
        dex_mod = stats.modifier(StatType.DEX)
        if dex_cap is not None:
            dex_mod = min(dex_mod, dex_cap)
        return self._recompute_attribute("ac") + dex_mod

    def compute_initiative(self, stats: Stats) -> int:
        """Derived initiative bonus."""
        return stats.modifier(StatType.DEX)

    def compute_speed(self, stats: Stats) -> float:  # noqa: ARG002
        """Base speed, possibly affected by conditions later."""
        return self._recompute_attribute("speed")

    def compute_advantage(self, prefix: str) -> int:
        return self._recompute_attribute(prefix + "_advantage")

    def add_modifier(self, modifier: Modifier) -> None:
        self._modifiers[modifier.attribute].append(modifier)

    def remove_modifier(self, source_id: str) -> None:
        for attr, mods in self._modifiers.items():
            self._modifiers[attr] = [m for m in mods if m.source_id != source_id]

    def _recompute_attribute(self, attr: str) -> Any:
        """Recompute the effective value from base + active modifiers."""
        base_value = getattr(self, f"base_{attr}")

        value = base_value
        for mod in self._modifiers[attr]:
            if mod.operation == "set":
                value = mod.value
            elif mod.operation == "add":
                value += mod.value
            elif mod.operation == "mul":
                value *= mod.value

        return value
