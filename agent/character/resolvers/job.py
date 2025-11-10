from agent.actions.registry import ActionRegistry
from agent.character.resolvers.base import CharacterBase
from agent.effects.registry import TraitRegistry
from agent.jobs.base import CharacterJob, JobFeature
from agent.jobs.feature import FeatureType
from agent.jobs.fighter import Fighter
from agent.jobs.spells import Spell
from agent.logs.log_event import LogLevel


class JobResolver(CharacterBase):
    job: CharacterJob = Fighter

    def change_job(self, job: CharacterJob) -> None:
        old_job = self.job

        # Remove old features
        for feature in old_job.get_features_for_level(self.level):
            self._remove_job_feature(feature)

        # Remove old spells
        for spell in old_job.get_spells_for_level(self.level):
            self._remove_spell(spell)

        # Remove proficiencies
        for prof in self.job.proficiencies:
            self.attributes.proficiencies.remove(prof)

        self.job = job
        self.apply_job_features()

        self.log_event(f"{self.name} changed from {old_job.type.value} to {job.type.value}", log_type=LogLevel.MAIN)

    def apply_job_features(self) -> None:
        """Register class features based on current level."""
        # TODO: The primary ability should depend on the type of class (fighter should not use STR)
        self.attributes.spellcasting_ability = self.job.primary_ability
        self.attributes.hit_die = self.job.hit_die

        for prof in self.job.proficiencies:
            if not self.attributes.has_proficiency(prof.target):
                self.attributes.proficiencies.append(prof)

        for feature in self.job.get_features_for_level(self.level):
            self._apply_job_feature(feature)

        for spell in self.job.get_spells_for_level(self.level):
            self._apply_spell(spell)

    def _apply_job_feature(self, feature: JobFeature) -> None:
        if feature.type == FeatureType.ACTIVE:
            if feature.ref_id not in {a.id for a in self.special_abilities}:
                action = ActionRegistry.create(
                    id_=feature.ref_id,
                    name=feature.name,
                    description=feature.description,
                    uses_per_rest=feature.uses_per_rest,
                    **feature.kwargs,
                )
                self.special_abilities.append(action)
                self.log_event(f"{self.name} gained ability {feature.name}", log_type=LogLevel.DETAIL)

        elif feature.type == FeatureType.PASSIVE:
            trait = TraitRegistry.create(
                feature_id=feature.ref_id,
                source_id=feature.name,
                name=feature.name,
                description=feature.description,
                **feature.kwargs,
            )
            self.register_passive(trait)

    def _remove_job_feature(self, feature: JobFeature) -> None:
        if feature.type == FeatureType.ACTIVE:
            self.special_abilities = [ability for ability in self.special_abilities if ability.id != feature.ref_id]
            self.log_event(f"{self.name} lost ability {feature.name}", log_type=LogLevel.DETAIL)

        elif feature.type == FeatureType.PASSIVE:
            self.unregister_passive(feature_id=feature.ref_id, source_id=feature.name)
            self.log_event(f"{self.name} lost passive trait {feature.name}", log_type=LogLevel.DETAIL)

    def _apply_spell(self, spell: Spell) -> None:
        if spell.ref_id not in {a.id for a in self.spells}:
            spell.ability = spell.ability or self.attributes.spellcasting_ability
            action = ActionRegistry.create(id_=spell.ref_id, **spell.model_dump(exclude={"type"}))
            self.spells.append(action)  # type: ignore[arg-type]
            self.log_event(f"{self.name} gained spell {action.name}", log_type=LogLevel.DETAIL)

    def _remove_spell(self, spell: Spell) -> None:
        self.spells = [s for s in self.spells if s.id != spell.ref_id]
        self.log_event(f"{self.name} lost spell {spell.ref_id}", log_type=LogLevel.DETAIL)
