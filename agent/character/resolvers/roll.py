from typing import Self

from pydantic import computed_field

from agent.character.resolvers.base import CharacterBase
from agent.character.stats import StatType
from agent.mechanics.advantage import resolve_advantage
from agent.mechanics.dice_roller import DiceRoll, DiceRoller

D20 = "1d20"


class RollResolver(CharacterBase):
    _dice: DiceRoller = DiceRoller()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def initiative_modifier(self) -> int:
        return self.attributes.initiative()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def proficiency_bonus(self) -> int:
        return self.attributes.proficiency_bonus(level=self.level)

    def initiative_roll(self) -> DiceRoll:
        expr = f"{D20}+{self.initiative_modifier}"
        return self._dice.roll_with_context(dice_expression=expr)

    def attack_roll(self, attack_stat: StatType, target: Self) -> DiceRoll:
        # Compute advantage from multiple sources
        sources = [
            self.attributes.stat_advantage(attack_stat),
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
        mod = self.attributes.stat_modifier(self.attributes.spellcasting_stat)
        expr = f"{expr}+{mod}"
        return self._dice.roll_with_context(dice_expression=expr)

    def save_roll(self, save_stat: StatType, *, is_spell: bool = False) -> DiceRoll:
        if self.attributes.save_autofail(save_stat):
            return DiceRoll(expression=D20, rolls=[1], total=1, raw=1)

        # Compute advantage from multiple sources
        sources = [
            self.attributes.stat_advantage(save_stat),
            self.attributes.stat_save_advantage(save_stat),
        ]
        if is_spell:
            sources.append(self.attributes.spell_save_advantage())
        advantage = resolve_advantage(sources)

        # Roll the d20 (with advantage/disadvantage if applicable)
        ability_mod = self.attributes.stat_modifier(save_stat)
        prof_bonus = self.proficiency_bonus if save_stat in self.attributes.save_proficiencies else 0
        mod = ability_mod + prof_bonus
        expr = f"{D20}+{mod}"
        return self._dice.roll_with_context(dice_expression=expr, advantage=advantage)

    def stealth_roll(self) -> DiceRoll:
        sources = [
            self.attributes.advantage("stealth"),
        ]
        advantage = resolve_advantage(sources)

        dex_mod = self.attributes.stat_modifier(StatType.DEX)
        expr = f"{D20}+{dex_mod}"
        return self._dice.roll_with_context(dice_expression=expr, advantage=advantage)

    def perception_roll(self) -> DiceRoll:
        sources = [self.attributes.advantage("perception")]
        advantage = resolve_advantage(sources)

        wis_mod = self.attributes.stat_modifier(StatType.WIS)
        expr = f"{D20}+{wis_mod}"

        return self._dice.roll_with_context(dice_expression=expr, advantage=advantage)

    def roll(self, expr: str) -> DiceRoll:
        return self._dice.roll_once(expr)
