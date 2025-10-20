from collections import defaultdict
from typing import Any, Literal

from pydantic import ConfigDict, Field, PrivateAttr

from agent.character.modifier import Modifier, ModifierRegistry
from agent.character.stats import Stats, StatType
from agent.equipment.armor import ArmorType
from agent.models.damage import DamageResistance, DamageType, DamageVulnerability


class Attributes(Stats):
    hp: int = 8
    spellcasting_stat: StatType = StatType.INT

    # Base scalar attributes
    base_hp: int = 8
    base_ac: int = 0
    base_speed: float = 6.0
    base_crit_roll_bonus: int = 0
    base_vision_range: float = 10.0
    base_spell_save_dc: int = 8

    # Base nested attributes
    base_advantage: defaultdict[str, bool] = Field(default_factory=lambda: defaultdict(lambda: False))
    base_disadvantage: defaultdict[str, bool] = Field(default_factory=lambda: defaultdict(lambda: False))
    base_save_advantage: defaultdict[str, bool] = Field(default_factory=lambda: defaultdict(lambda: False))
    base_save_disadvantage: defaultdict[str, bool] = Field(default_factory=lambda: defaultdict(lambda: False))
    base_save_autofail: defaultdict[str, bool] = Field(default_factory=lambda: defaultdict(lambda: False))
    base_resistance: defaultdict[str, float] = Field(default_factory=lambda: defaultdict(lambda: 0.0))
    base_vulnerability: defaultdict[str, float] = Field(default_factory=lambda: defaultdict(lambda: 0.0))

    _registry: ModifierRegistry = PrivateAttr(default_factory=ModifierRegistry)

    model_config = ConfigDict(extra="allow")  # To mock during tests

    def max_hp(self, level: int) -> int:
        """HP grows with level and Constitution modifier."""
        return self.base_hp + (level - 1) * (5 + self.stat_modifier(StatType.CON))

    def ac_bonus(self, armor_type: ArmorType | None, max_dex_bonus: int | None = 2) -> int:
        """Compute Armor Class bonus from modifiers."""
        ac = self._recompute_attribute("ac")
        dex_mod = self.stat_modifier(StatType.DEX)

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
        return self.stat_modifier(StatType.DEX)

    def proficiency_bonus(self, level: int) -> int:
        return 2 + (level - 1) // 4

    def speed(self) -> float:
        """Base speed, possibly affected by conditions later."""
        return self._recompute_attribute("speed")

    def crit_roll(self) -> int:
        crit_roll = 20
        return crit_roll - self._recompute_attribute("crit_roll_bonus")

    def advantage(self, kind: str) -> int:
        adv = self._recompute_attribute(f"advantage.{kind}")
        dis = self._recompute_attribute(f"disadvantage.{kind}")
        return int(adv) - int(dis)

    def spell_save_dc(self, level: int) -> int:
        dc = self._recompute_attribute("spell_save_dc")
        spell_mod = self.stat_modifier(self.spellcasting_stat)
        prof = self.proficiency_bonus(level=level)
        return dc + prof + spell_mod

    def spell_save_advantage(self) -> int:
        adv = self._recompute_attribute("save_advantage.spell")
        dis = self._recompute_attribute("save_disadvantage.spell")
        return int(adv) - int(dis)

    def stat_save_advantage(self, stat: StatType) -> int:
        adv = self._recompute_attribute(f"save_advantage.{stat.name.lower()}")
        dis = self._recompute_attribute(f"save_disadvantage.{stat.name.lower()}")
        return int(adv) - int(dis)

    def save_autofail(self, stat: StatType) -> bool:
        return self._recompute_attribute(f"save_autofail.{stat.name.lower()}")

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
            base_name, key = attr.split(".", 1)
            base_dict = getattr(self, f"base_{base_name}")
            base_value = base_dict[key]
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
