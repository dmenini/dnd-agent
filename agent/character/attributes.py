from typing import Any, Literal

from pydantic import ConfigDict, PrivateAttr

from agent.character.abilities import Abilities, AbilityType
from agent.character.modifier import Modifier, ModifierRegistry
from agent.character.proficiency import Proficiency
from agent.equipment.armor import ArmorType
from agent.models.damage import DamageResistance, DamageType, DamageVulnerability


class Attributes(Abilities):
    hp: int = 15
    spellcasting_ability: AbilityType = AbilityType.INT
    proficiencies: list[Proficiency] = []

    # Base attributes
    base_hp: int = 15
    base_ac: int = 0
    base_speed: float = 6.0
    base_crit_roll_bonus: int = 0
    base_vision_range: float = 10.0
    base_vision_fov: float = 120.0
    base_perception: int = 10
    base_spell_save_dc: int = 8
    base_proficiency_bonus: int = 2
    base_advantage: bool = False
    base_disadvantage: bool = False
    base_save_advantage: bool = False
    base_save_disadvantage: bool = False
    base_save_autofail: bool = False
    base_resistance: float = 0.0
    base_vulnerability: float = 0.0
    base_ac_mod: bool = False  # Extra AC ability modifier

    _registry: ModifierRegistry = PrivateAttr(default_factory=ModifierRegistry)

    model_config = ConfigDict(extra="allow")  # To mock during tests

    def max_hp(self, level: int) -> int:
        """HP grows with level and Constitution modifier."""
        return self.base_hp + (level - 1) * (5 + self.ability_modifier(AbilityType.CON))

    def ac_bonus(self, armor_type: ArmorType | None, max_dex_bonus: int | None = 2) -> int:
        """Compute Armor Class bonus from modifiers."""
        ac = self._recompute_attribute("ac")
        dex_mod = self.ability_modifier(AbilityType.DEX)

        # Apply CON modifier to AC if the character has that feature
        if self._recompute_attribute(f"ac_mod.{AbilityType.CON.name.lower()}"):
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
        bonus = self._recompute_attribute("proficiency_bonus")
        return bonus + (level - 1) // 4

    def speed(self) -> float:
        return self._recompute_attribute("speed")

    def crit_roll(self) -> int:
        crit_roll = 20
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
        adv = self._recompute_attribute(f"save_advantage.{ability.name.lower()}")
        dis = self._recompute_attribute(f"save_disadvantage.{ability.name.lower()}")
        return int(adv) - int(dis)

    def save_autofail(self, stat: AbilityType) -> bool:
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
