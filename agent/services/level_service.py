"""Level service - handles character leveling and progression."""
import math
from typing import TYPE_CHECKING

from agent.character.abilities import AbilityType
from agent.logs.log_event import LogLevel
from agent.services.job_service import JobService

if TYPE_CHECKING:
    from agent.character.character import Character


class LevelService:
    """Stateless service for character level progression."""

    @classmethod
    def level_up(cls, character: "Character") -> None:
        """Level up a character by one level, applying new features and scaling resources.

        Args:
            character: The character to level up

        Note:
            - Increments character level
            - Applies newly unlocked features, passives, and spells
            - Updates HP to new maximum
            - Recomputes spell slots
            - Updates proficiency bonus (automatic via level)
        """
        old_level = character.level
        new_level = old_level + 1
        character.level = new_level

        character.log_event(
            f"{character.name} advanced to level {new_level}!",
            log_type=LogLevel.MAIN,
        )

        # Get features/passives/spells that just became available at this level
        new_features = [f for f in character.job.features if f.level_required == new_level]
        new_passives = [p for p in character.job.passives if p.level_required == new_level]
        new_spells = [s for s in character.job.spells if s.level_required == new_level]

        # Apply newly unlocked features
        for feature in new_features:
            JobService.apply_job_feature(character, feature)

        for passive in new_passives:
            JobService.apply_job_passive(character, passive)

        for spell in new_spells:
            JobService.apply_spell(character, spell)

        # Calculate HP increase: average of hit die + CON modifier
        # In D&D, level up grants either a roll or fixed value (we use fixed: (hit_die/2 + 1) + CON)

        hp_gain_from_die = math.ceil(character.attributes.hit_die / 2) + 1
        con_modifier = character.attributes.ability_modifier(AbilityType.CON)
        hp_increase = hp_gain_from_die + con_modifier

        # Update HP
        character.attributes.hp += hp_increase
        new_max_hp = character.max_hp

        # Ensure HP doesn't exceed new max
        character.attributes.hp = min(character.attributes.hp, new_max_hp)

        character.log_event(
            f"HP increased by {hp_increase} (now {character.attributes.hp}/{new_max_hp})",
            log_type=LogLevel.DETAIL,
        )

        # Recompute spell slots for new level
        character.spell_slots.recompute(new_level)
        if character.spell_slots.max_slots:
            character.log_event(f"Spell slots updated: {character.spell_slots}", log_type=LogLevel.DETAIL)

        # Proficiency bonus automatically updates via level (computed in proficiency_bonus method)
        prof_bonus = character.attributes.proficiency_bonus(new_level)
        if prof_bonus > character.attributes.proficiency_bonus(old_level):
            character.log_event(f"Proficiency bonus increased to +{prof_bonus}", log_type=LogLevel.DETAIL)

    @classmethod
    def set_level(cls, character: "Character", target_level: int) -> None:
        """Set character to a specific level, applying all appropriate features.

        Args:
            character: The character to level
            target_level: The target level (must be >= 1)

        Note:
            This is useful for testing or setting up characters at specific levels.
            Repeatedly calls level_up() until target is reached.
        """
        if target_level < 1:
            msg = f"Target level must be >= 1, got {target_level}"
            raise ValueError(msg)

        if target_level < character.level:
            msg = "Level reduction not supported - create a new character instead"
            raise ValueError(msg)

        # Level up until we reach target
        while character.level < target_level:
            cls.level_up(character)
