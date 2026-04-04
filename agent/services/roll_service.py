"""Roll service - stateless dice rolling logic extracted from Character."""

import re
from typing import TYPE_CHECKING

from agent.character.abilities import AbilityType, SkillType
from agent.equipment.armor import ArmorType
from agent.equipment.base import EquipmentType
from agent.equipment.weapons import WeaponType
from agent.mechanics.advantage import resolve_advantage
from agent.mechanics.dice_roller import DiceRoll, DiceRoller
from agent.models.enums import Advantage

if TYPE_CHECKING:
    from agent.character.character import Character

D20 = "1d20"


class RollService:
    """Stateless service for all dice rolling operations."""

    _dice: DiceRoller = DiceRoller()

    @classmethod
    def _get_dice(cls, character: "Character") -> DiceRoller:
        """Get dice roller - uses character's cheater_dice if available (for tests)."""
        return character.cheater_dice if character.cheater_dice is not None else cls._dice

    @classmethod
    def initiative_roll(cls, character: "Character") -> DiceRoll:
        """Roll initiative for a character."""
        modifier = character.attributes.initiative()
        expr = f"{D20}+{modifier}"
        return cls._get_dice(character).roll_with_context(dice_expression=expr)

    @classmethod
    def attack_roll(
        cls, character: "Character", ability: AbilityType, weapon: WeaponType, target: "Character"
    ) -> DiceRoll:
        """Roll an attack against a target."""
        # Compute advantage from multiple sources
        sources = [
            character.attributes.ability_advantage(ability),
            character.attributes.advantage("attack"),
            target.attributes.advantage("defense"),
            cls._armor_advantage(character, ability),
        ]
        advantage = resolve_advantage(sources)

        ability_mod = character.attributes.ability_modifier(ability)
        prof_bonus = character.proficiency_bonus(weapon)
        mod = ability_mod + prof_bonus
        expr = f"{D20}+{mod}"

        return cls._get_dice(character).roll_with_context(dice_expression=expr, advantage=advantage)

    @classmethod
    def damage_roll(
        cls, character: "Character", *, damage_dice: str, ability: AbilityType, is_critical: bool = False
    ) -> DiceRoll:
        """Roll damage with ability modifier."""
        # Parse existing modifier from the dice expression (e.g. "1d8+2" → base="1d8", base_mod=2)
        match = re.match(r"^(\d+d\d+)([+-]\d+)?$", damage_dice.strip())
        if match:
            base_expr, base_mod_str = match.groups()
            base_mod = int(base_mod_str) if base_mod_str else 0
        else:
            base_expr = damage_dice
            base_mod = 0

        ability_mod = character.attributes.ability_modifier(ability)
        mod = base_mod + ability_mod
        expr = f"{base_expr}+{mod}"

        dice = cls._get_dice(character)
        if is_critical:
            return dice.roll_twice(expr)
        return dice.roll_once(expr)

    @classmethod
    def heal_roll(cls, character: "Character", expr: str) -> DiceRoll:
        """Roll healing with spellcasting modifier."""
        if character.attributes.spellcasting_ability is None:
            msg = f"{character.name} cannot perform healing rolls without a spellcasting ability."
            raise ValueError(msg)

        mod = character.attributes.ability_modifier(character.attributes.spellcasting_ability)
        expr = f"{expr}+{mod}"
        return cls._get_dice(character).roll_with_context(dice_expression=expr)

    @classmethod
    def save_roll(cls, character: "Character", ability: AbilityType, *, is_spell: bool = False) -> DiceRoll:
        """Roll a saving throw."""
        if character.attributes.save_autofail(ability):
            return DiceRoll(expression=D20, rolls=[1], total=1, raw=1)

        # Compute advantage from multiple sources
        sources = [
            character.attributes.ability_advantage(ability),
            character.attributes.ability_save_advantage(ability),
            cls._armor_advantage(character, ability),
        ]
        if is_spell:
            sources.append(character.attributes.spell_save_advantage())
        advantage = resolve_advantage(sources)

        # Roll the d20 (with advantage/disadvantage if applicable)
        ability_mod = character.attributes.ability_modifier(ability)
        prof_bonus = character.proficiency_bonus(ability)
        mod = ability_mod + prof_bonus
        expr = f"{D20}+{mod}"
        return cls._get_dice(character).roll_with_context(dice_expression=expr, advantage=advantage)

    @classmethod
    def skill_check(cls, character: "Character", skill: SkillType) -> DiceRoll:
        """Roll a skill check."""
        ability = skill.to_ability()

        sources = [character.attributes.advantage(skill.value), cls._armor_advantage(character, ability)]
        advantage = resolve_advantage(sources)

        ability_mod = character.attributes.ability_modifier(ability)
        prof_bonus = character.proficiency_bonus(skill)
        mod = ability_mod + prof_bonus
        return cls._get_dice(character).roll_with_context(dice_expression=f"{D20}+{mod}", advantage=advantage)

    @classmethod
    def stealth_roll(cls, character: "Character") -> DiceRoll:
        """Roll stealth check."""
        return cls.skill_check(character, skill=SkillType.STEALTH)

    @classmethod
    def perception_roll(cls, character: "Character") -> DiceRoll:
        """Roll perception check."""
        return cls.skill_check(character, skill=SkillType.PERCEPTION)

    @classmethod
    def roll(cls, expr: str, character: "Character | None" = None) -> DiceRoll:
        """Roll a generic dice expression."""
        dice = cls._get_dice(character) if character else cls._dice
        return dice.roll_once(expr)

    @staticmethod
    def _armor_advantage(character: "Character", ability: AbilityType) -> int:
        """Check if armor proficiency affects the roll."""
        penalty = ability in {AbilityType.DEX, AbilityType.STR} and (
            (
                character.equipment.armor is not None
                and not character.attributes.has_proficiency(character.equipment.armor.armor_type)
            )
            or (
                character.equipment.off_hand is not None
                and character.equipment.off_hand.type == EquipmentType.SHIELD
                and not character.attributes.has_proficiency(ArmorType.SHIELD)
            )
        )
        return Advantage.DISADVANTAGE if penalty else Advantage.NEUTRAL
