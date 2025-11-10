from typing import Self

from pydantic import computed_field

from agent.character.abilities import AbilityType, SkillType
from agent.character.resolvers.base import CharacterBase
from agent.mechanics.advantage import resolve_advantage
from agent.mechanics.dice_roller import DiceRoll, DiceRoller

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

    def attack_roll(self, ability: AbilityType, target: Self) -> DiceRoll:
        # Compute advantage from multiple sources
        sources = [
            self.attributes.ability_advantage(ability),
            self.attributes.advantage("attack"),
            target.attributes.advantage("defense"),
        ]
        advantage = resolve_advantage(sources)

        return self._dice.roll_with_context(dice_expression=D20, advantage=advantage)

    def damage_roll(self, *, expr: str, is_critical: bool = False) -> DiceRoll:
        if is_critical:
            return self._dice.roll_twice(expr)
        return self._dice.roll_once(expr)

    def heal_roll(self, expr: str) -> DiceRoll:
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

        sources = [self.attributes.advantage(skill.value)]
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
