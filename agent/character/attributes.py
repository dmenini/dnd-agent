import math
from enum import Enum
from typing import Any, Literal

from pydantic import ConfigDict, PrivateAttr

from agent.character.abilities import Abilities, AbilityType
from agent.character.modifier import Modifier, ModifierRegistry
from agent.character.proficiency import Proficiency
from agent.equipment.armor import ArmorType
from agent.models.constants import (
    DEFAULT_CRIT_ROLL,
    DEFAULT_PERCEPTION,
    DEFAULT_PROFICIENCY_BONUS,
    DEFAULT_SPEED,
    DEFAULT_SPELL_SAVE_DIFFICULTY_CLASS,
    DEFAULT_VISION_FOV,
    DEFAULT_VISION_RANGE,
)
from agent.models.damage import DamageResistance, DamageType, DamageVulnerability


class Attributes(Abilities):
    hp: int = -1
    spellcasting_ability: AbilityType = AbilityType.INT
    proficiencies: list[Proficiency] = []
    hit_die: int = 0

    # Base attributes on which modifiers are applied (do not change directly)
    base_hp: int = 0
    base_ac: int = 0
    base_speed: float = DEFAULT_SPEED
    base_crit_roll_bonus: int = 0
    base_vision_range: float = DEFAULT_VISION_RANGE
    base_vision_fov: float = DEFAULT_VISION_FOV
    base_perception: int = DEFAULT_PERCEPTION
    base_spell_save_dc: int = DEFAULT_SPELL_SAVE_DIFFICULTY_CLASS
    base_expertise: bool = False
    base_advantage: bool = False
    base_disadvantage: bool = False
    base_save_advantage: bool = False
    base_save_disadvantage: bool = False
    base_save_autofail: bool = False
    base_resistance: float = 0.0
    base_vulnerability: float = 0.0
    base_ac_mod: bool = False  # Whether there is an extra AC ability modifier (in addition to DEX)

    _registry: ModifierRegistry = PrivateAttr(default=ModifierRegistry())

    model_config = ConfigDict(extra="allow")  # To mock during tests

    def max_hp(self, level: int) -> int:
        """HP grows with level and Constitution modifier."""
        bonus_hp = self._recompute_attribute("hp")
        level1_hp = self.hit_die + self.ability_modifier(AbilityType.CON)
        per_level_increase = math.ceil(self.hit_die / 2) + 1 + self.ability_modifier(AbilityType.CON)
        return level1_hp + (level - 1) * per_level_increase + bonus_hp

    def ac_bonus(self, armor_type: ArmorType | None, max_dex_bonus: int | None = 2) -> int:
        """Compute Armor Class bonus from modifiers."""
        ac = self._recompute_attribute("ac")
        dex_mod = self.ability_modifier(AbilityType.DEX)

        # Apply CON modifier to AC if the character has that feature
        if self._recompute_attribute(f"ac_mod.{AbilityType.CON}"):
            ac += self.ability_modifier(AbilityType.CON)

        if not armor_type:
            ac += 10 + dex_mod
        elif armor_type == ArmorType.LIGHT:
            ac += dex_mod
        elif armor_type == ArmorType.MEDIUM:
            dex_bonus = min(dex_mod, max_dex_bonus or 2)
            ac += dex_bonus

        return ac

    def initiative(self) -> int:
        """Derived initiative bonus."""
        return self.ability_modifier(AbilityType.DEX)

    def proficiency_bonus(self, level: int) -> int:
        return DEFAULT_PROFICIENCY_BONUS + (level - 1) // 4

    def has_proficiency(self, reference: Enum) -> bool:
        return any(prof.target == reference for prof in self.proficiencies)

    def has_expertise(self, reference: Enum) -> bool:
        return self._recompute_attribute(f"expertise.{reference.value}")

    def speed(self) -> float:
        return self._recompute_attribute("speed")

    def crit_roll(self) -> int:
        crit_roll = DEFAULT_CRIT_ROLL
        return crit_roll - self._recompute_attribute("crit_roll_bonus")

    def passive_perception(self) -> int:
        wis_mod = self.ability_modifier(AbilityType.WIS)
        return self._recompute_attribute("perception") + wis_mod

    def vision_range(self) -> float:
        return self._recompute_attribute("vision_range")

    def advantage(self, kind: str) -> int:
        adv = self._recompute_attribute(f"advantage.{kind}")
        dis = self._recompute_attribute(f"disadvantage.{kind}")
        return int(adv) - int(dis)

    def spell_save_dc(self, level: int) -> int:
        dc = self._recompute_attribute("spell_save_dc")
        spell_mod = self.ability_modifier(self.spellcasting_ability)
        prof = self.proficiency_bonus(level=level)
        return dc + prof + spell_mod

    def spell_save_advantage(self) -> int:
        adv = self._recompute_attribute("save_advantage.spell")
        dis = self._recompute_attribute("save_disadvantage.spell")
        return int(adv) - int(dis)

    def ability_save_advantage(self, ability: AbilityType) -> int:
        adv = self._recompute_attribute(f"save_advantage.{ability.value}")
        dis = self._recompute_attribute(f"save_disadvantage.{ability.value}")
        return int(adv) - int(dis)

    def save_autofail(self, ability: AbilityType) -> bool:
        return self._recompute_attribute(f"save_autofail.{ability.value}")

    def damage_resistance(self, dtype: DamageType) -> DamageResistance | None:
        value = self._recompute_attribute(f"resistance.{dtype.value}")
        if not value:
            return None
        return DamageResistance(value=value, type=dtype)

    def damage_vulnerability(self, dtype: DamageType) -> DamageVulnerability | None:
        value = self._recompute_attribute(f"vulnerability.{dtype.value}")
        if not value:
            return None
        return DamageVulnerability(value=value, type=dtype)

    def get_modifiers(self, attr: str) -> list[Modifier]:
        return self._registry.get(attr)

    def add_modifier(self, modifier: Modifier, stacking_rule: Literal["min", "max", "sum"] = "sum") -> None:
        self._registry.add(modifier, stacking_rule)

    def remove_modifier(self, source_id: str) -> Modifier | None:
        return self._registry.remove(source_id)

    def _recompute_attribute(self, attr: str) -> Any:
        """
        Recompute the effective value from base + active modifiers.
        Supports nested attributes (e.g. 'save_advantage.STR', 'resistance.fire').
        Priority: Additive factors -> Multiplicative factors -> Override with last.
        """
        if "." in attr:
            base_name, _ = attr.split(".", 1)
            base_value = getattr(self, f"base_{base_name}")
        else:
            base_value = getattr(self, f"base_{attr}")

        # Priority: add -> mul -> set
        add_mod = self._registry.stack(attr, "add")
        mul_mod = self._registry.stack(attr, "mul")

        value = (base_value + add_mod) * mul_mod

        override_val = self._registry.stack(attr, "set")
        if override_val:
            value = override_val

        return value
