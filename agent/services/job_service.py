"""Job service - stateless job and class feature management."""

from typing import TYPE_CHECKING

from agent.actions.base import ActionCategory
from agent.actions.common.spell import BonusSupportSpellAction
from agent.character.abilities import AbilityType
from agent.jobs.base import CharacterJob, JobFeature
from agent.jobs.feature import JobPassive
from agent.jobs.spells import Spell, SpellType, spell_action_map
from agent.logs.log_event import LogLevel
from agent.models.enums import FeatureId
from agent.services.trait_service import TraitService

if TYPE_CHECKING:
    from agent.character.character import Character


class JobService:
    """Stateless service for managing character jobs, features, and spells.

    Handles job changes, applying job features, learning spells, and managing
    job-related proficiencies and resources.
    """

    @classmethod
    def change_job(cls, character: "Character", job: CharacterJob) -> None:
        """Change a character's job.

        Args:
            character: The character changing jobs
            job: The new job to switch to
        """
        old_job = character.job

        # Remove old features
        for feature in old_job.get_features_for_level(character.level):
            cls.remove_job_feature(character, feature)

        # Remove old spells
        for spell in old_job.get_spells_for_level(character.level):
            cls.remove_spell(character, spell)

        # Remove proficiencies
        for prof in character.job.proficiencies:
            character.attributes.proficiencies.remove(prof)

        character.job = job
        cls.apply_job_features(character)

        character.log_event(
            f"{character.name} changed from {old_job.type.value} to {job.type.value}", log_type=LogLevel.MAIN
        )

    @classmethod
    def apply_job_features(cls, character: "Character") -> None:
        """Register class features based on current level.

        Args:
            character: The character to apply job features to
        """
        character.attributes.spellcasting_ability = character.job.spellcasting_ability
        character.attributes.hit_die = character.job.hit_die

        for prof in character.job.proficiencies:
            if not character.attributes.has_proficiency(prof.target):
                character.attributes.proficiencies.append(prof)

        for feature in character.job.get_features_for_level(character.level):
            cls.apply_job_feature(character, feature)

        for passive in character.job.get_passives_for_level(character.level):
            cls.apply_job_passive(character, passive)

        for spell in character.job.get_spells_for_level(character.level):
            cls.apply_spell(character, spell)

        character.spell_slots.progression = character.job.spell_progression
        character.spell_slots.recompute(character.level)

    @classmethod
    def apply_job_feature(cls, character: "Character", feature: JobFeature) -> None:
        """Apply a job feature (special ability).

        Args:
            character: The character learning the feature
            feature: The feature to apply
        """
        if feature.ref_id not in {a.id for a in character.special_abilities}:
            action = feature.to_action()

            # Special handling for War Priest: set uses_per_rest based on WIS modifier
            if feature.ref_id == FeatureId.WAR_PRIEST and hasattr(action, "uses_per_rest"):
                wis_mod = character.attributes.ability_modifier(AbilityType.WIS)
                action.uses_per_rest = max(1, wis_mod)  # type: ignore[attr-defined]

            character.special_abilities.append(action)
            character.log_event(f"{character.name} learnt ability {feature.name}", log_type=LogLevel.DETAIL)

    @classmethod
    def remove_job_feature(cls, character: "Character", feature: JobFeature) -> None:
        """Remove a job feature.

        Args:
            character: The character forgetting the feature
            feature: The feature to remove
        """
        character.special_abilities = [
            ability for ability in character.special_abilities if ability.id != feature.ref_id
        ]
        character.log_event(f"{character.name} forgot ability {feature.name}", log_type=LogLevel.DETAIL)

    @classmethod
    def apply_job_passive(cls, character: "Character", passive: JobPassive) -> None:
        """Apply a job passive trait.

        Args:
            character: The character gaining the passive
            passive: The passive to apply
        """
        passive.trait.source_id = character.job.type.value
        TraitService.register_passive(character, passive.trait)

    @classmethod
    def remove_job_passive(cls, character: "Character", passive: JobPassive) -> None:
        """Remove a job passive trait.

        Args:
            character: The character losing the passive
            passive: The passive to remove
        """
        TraitService.unregister_passive(
            character, feature_id=passive.trait.feature_id, source_id=character.job.type.value
        )

    @classmethod
    def apply_spell(cls, character: "Character", spell: Spell) -> None:
        """Learn a spell.

        Args:
            character: The character learning the spell
            spell: The spell to learn
        """
        if character.attributes.spellcasting_ability is None:
            msg = "Character is not a caster and cannot learn spells"
            raise ValueError(msg)

        if spell.ref_id not in {a.id for a in character.spells}:
            spell.ability = spell.ability or character.attributes.spellcasting_ability
            # Use BonusSupportSpellAction for bonus action support spells
            if spell.spell_type == SpellType.SUPPORT and spell.casting_time == ActionCategory.BONUS:
                action = BonusSupportSpellAction(id=spell.ref_id.value, **spell.model_dump(exclude={"type"}))
            else:
                action = spell_action_map[spell.spell_type](id=spell.ref_id.value, **spell.model_dump(exclude={"type"}))
            character.spells.append(action)  # type: ignore[arg-type]
            character.log_event(f"{character.name} learnt spell {action.name}", log_type=LogLevel.DETAIL)

    @classmethod
    def remove_spell(cls, character: "Character", spell: Spell) -> None:
        """Forget a spell.

        Args:
            character: The character forgetting the spell
            spell: The spell to forget
        """
        character.spells = [s for s in character.spells if s.id != spell.ref_id]
        character.log_event(f"{character.name} forgot spell {spell.ref_id}", log_type=LogLevel.DETAIL)
