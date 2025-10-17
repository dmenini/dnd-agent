import builtins
from collections import defaultdict
from typing import Any, Literal

from pydantic import BaseModel, Field, PrivateAttr

from agent.character.stats import Stats, StatType
from agent.models.damage import DamageResistance, DamageType, DamageVulnerability


class Modifier(BaseModel):
    source_id: str
    attribute: str
    value: Any
    operation: Literal["set", "add", "mul"] = "set"


class ModifierRegistry(BaseModel):
    _modifiers: dict[str, list[Modifier]] = PrivateAttr(default_factory=dict)
    _stacking_rules: dict[str, Literal["sum", "min", "max"]] = PrivateAttr(default_factory=dict)

    def add(self, modifier: Modifier, stacking_rule: Literal["sum", "min", "max"] = "sum") -> None:
        attr = modifier.attribute
        if attr not in self._modifiers:
            self._modifiers[attr] = []
            self._stacking_rules[attr] = stacking_rule
        self._modifiers[attr].append(modifier)

    def remove(self, source_id: str) -> None:
        for attr, mods in list(self._modifiers.items()):
            self._modifiers[attr] = [m for m in mods if m.source_id != source_id]
            if not self._modifiers[attr]:
                del self._modifiers[attr]
                del self._stacking_rules[attr]

    def get(self, attr: str) -> list[Modifier]:
        return self._modifiers.get(attr, [])

    def attributes(self) -> list[str]:
        """Return all attributes currently affected by modifiers."""
        return list(self._modifiers.keys())

    def stack(self, attr: str, op: Literal["set", "add", "mul"]) -> Any:
        """
        Select a final modifier value for the given attribute and operation based on the configured stacking rule.
        """
        neutral_el = 1 if op == "mul" else 0
        mods = self._modifiers.get(attr, [])
        if not mods:
            return neutral_el

        if op == "set":
            # Most recent 'set' overrides previous ones
            for mod in reversed(mods):
                if mod.operation == op:
                    return mod.value
            return None

        stacking_rule = self._stacking_rules[attr]
        mode_fn = getattr(builtins, stacking_rule)
        return mode_fn(mod.value for mod in mods if mod.operation == op) or neutral_el


class Attributes(BaseModel):
    hp: int = 8

    # Base scalar attributes
    base_hp: int = 8
    base_ac: int = 2
    base_speed: float = 6.0
    base_crit_roll_bonus: int = 0
    base_vision_range: float = 10.0

    # Base nested attributes
    base_advantage: defaultdict[str, bool] = Field(default_factory=lambda: defaultdict(lambda: False))
    base_disadvantage: defaultdict[str, bool] = Field(default_factory=lambda: defaultdict(lambda: False))
    base_save_advantage: defaultdict[str, bool] = Field(default_factory=lambda: defaultdict(lambda: False))
    base_save_disadvantage: defaultdict[str, bool] = Field(default_factory=lambda: defaultdict(lambda: False))
    base_save_autofail: defaultdict[str, bool] = Field(default_factory=lambda: defaultdict(lambda: False))
    base_resistance: defaultdict[str, float] = Field(default_factory=lambda: defaultdict(lambda: 0.0))
    base_vulnerability: defaultdict[str, float] = Field(default_factory=lambda: defaultdict(lambda: 0.0))

    _registry: ModifierRegistry = PrivateAttr(default_factory=ModifierRegistry)

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

    def compute_crit_roll(self) -> int:
        crit_roll = 20
        return crit_roll - self._recompute_attribute("crit_roll_bonus")

    def compute_advantage(self, kind: str) -> int:
        adv = self._recompute_attribute(f"advantage.{kind}")
        dis = self._recompute_attribute(f"disadvantage.{kind}")
        return int(adv) - int(dis)

    def compute_save_advantage(self, stat: StatType) -> int:
        adv = self._recompute_attribute(f"save_advantage.{stat.name.lower()}")
        dis = self._recompute_attribute(f"save_disadvantage.{stat.name.lower()}")
        return int(adv) - int(dis)

    def compute_save_autofail(self, stat: StatType) -> bool:
        return self._recompute_attribute(f"save_autofail.{stat.name.lower()}")

    def compute_resistance(self, dtype: DamageType) -> DamageResistance:
        value = self._recompute_attribute(f"resistance.{dtype.value}")
        return DamageResistance(value=value, type=dtype)

    def compute_vulnerability(self, dtype: DamageType) -> DamageVulnerability:
        value = self._recompute_attribute(f"vulnerability.{dtype.value}")
        return DamageVulnerability(value=value, type=dtype)

    def get_modifiers(self, attr: str) -> list[Modifier]:
        return self._registry.get(attr)

    def add_modifier(self, modifier: Modifier, stacking_rule: Literal["min", "max", "sum"] = "sum") -> None:
        self._registry.add(modifier, stacking_rule)

    def remove_modifier(self, source_id: str) -> None:
        self._registry.remove(source_id)

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
