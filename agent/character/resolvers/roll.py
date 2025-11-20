import re
from typing import Self

from pydantic import computed_field

from agent.character.abilities import AbilityType, SkillType
from agent.character.resolvers.base import CharacterBase
from agent.equipment.armor import ArmorType
from agent.equipment.base import EquipmentType
from agent.equipment.weapons import WeaponType
from agent.mechanics.advantage import resolve_advantage
from agent.mechanics.dice_roller import DiceRoll, DiceRoller
from agent.models.enums import Advantage

D20 = "1d20"


class RollResolver(CharacterBase):
    _dice: DiceRoller = DiceRoller()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def initiative_modifier(self) -> int:
        return self.attributes.initiative()

    def initiative_roll(self) -> DiceRoll:
        expr = f"{D20}+{self.initiative_modifier}"
        return self._dice.roll_with_context(dice_expression=expr)

    def _armor_advantage(self, ability: AbilityType) -> int:
        penalty = ability in {AbilityType.DEX, AbilityType.STR} and (
            (self.armor is not None and not self.attributes.has_proficiency(self.armor.armor_type))
            or (
                self.off_hand is not None
                and self.off_hand.type == EquipmentType.SHIELD
                and not self.attributes.has_proficiency(ArmorType.SHIELD)
            )
        )
        return Advantage.DISADVANTAGE if penalty else Advantage.NEUTRAL

    def attack_roll(self, ability: AbilityType, weapon: WeaponType, target: Self) -> DiceRoll:
        # Compute advantage from multiple sources
        sources = [
            self.attributes.ability_advantage(ability),
            self.attributes.advantage("attack"),
            target.attributes.advantage("defense"),
            self._armor_advantage(ability),
        ]
        advantage = resolve_advantage(sources)

        ability_mod = self.attributes.ability_modifier(ability)
        prof_bonus = self.proficiency_bonus(weapon)
        mod = ability_mod + prof_bonus
        expr = f"{D20}+{mod}"

        return self._dice.roll_with_context(dice_expression=expr, advantage=advantage)

    def damage_roll(self, *, damage_dice: str, ability: AbilityType, is_critical: bool = False) -> DiceRoll:
        # Parse existing modifier from the dice expression (e.g. "1d8+2" → base="1d8", base_mod=2)
        match = re.match(r"^(\d+d\d+)([+-]\d+)?$", damage_dice.strip())
        if match:
            base_expr, base_mod_str = match.groups()
            base_mod = int(base_mod_str) if base_mod_str else 0
        else:
            base_mod = 0

        ability_mod = self.attributes.ability_modifier(ability)
        mod = base_mod + ability_mod
        expr = f"{damage_dice}+{mod}"

        if is_critical:
            return self._dice.roll_twice(expr)
        return self._dice.roll_once(expr)

    def heal_roll(self, expr: str) -> DiceRoll:
        if self.attributes.spellcasting_ability is None:
            msg = f"{self.name} cannot perform healing rolls without a spellcasting ability."
            raise ValueError(msg)

        mod = self.attributes.ability_modifier(self.attributes.spellcasting_ability)
        expr = f"{expr}+{mod}"
        return self._dice.roll_with_context(dice_expression=expr)

    def save_roll(self, ability: AbilityType, *, is_spell: bool = False) -> DiceRoll:
        if self.attributes.save_autofail(ability):
            return DiceRoll(expression=D20, rolls=[1], total=1, raw=1)

        # Compute advantage from multiple sources
        sources = [
            self.attributes.ability_advantage(ability),
            self.attributes.ability_save_advantage(ability),
            self._armor_advantage(ability),
        ]
        if is_spell:
            sources.append(self.attributes.spell_save_advantage())
        advantage = resolve_advantage(sources)

        # Roll the d20 (with advantage/disadvantage if applicable)
        ability_mod = self.attributes.ability_modifier(ability)
        prof_bonus = self.proficiency_bonus(ability)
        mod = ability_mod + prof_bonus
        expr = f"{D20}+{mod}"
        return self._dice.roll_with_context(dice_expression=expr, advantage=advantage)

    def skill_check(self, skill: SkillType) -> DiceRoll:
        ability = skill.to_ability()

        sources = [self.attributes.advantage(skill.value), self._armor_advantage(ability)]
        advantage = resolve_advantage(sources)

        ability_mod = self.attributes.ability_modifier(ability)
        prof_bonus = self.proficiency_bonus(skill)
        mod = ability_mod + prof_bonus
        return self._dice.roll_with_context(dice_expression=f"{D20}+{mod}", advantage=advantage)

    def stealth_roll(self) -> DiceRoll:
        return self.skill_check(skill=SkillType.STEALTH)

    def perception_roll(self) -> DiceRoll:
        return self.skill_check(skill=SkillType.PERCEPTION)

    def roll(self, expr: str) -> DiceRoll:
        return self._dice.roll_once(expr)
