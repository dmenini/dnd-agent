from agent.actions.base import Action
from agent.actions.common.spell import AttackSpellAction, SupportSpellAction
from agent.actions.registry import ActionRegistry
from agent.character.resolvers.base import CharacterBase
from agent.effects.registry import TraitRegistry
from agent.jobs.base import CharacterJob, JobFeature
from agent.jobs.feature import FeatureType
from agent.jobs.fighter import Fighter
from agent.jobs.spells import Spell
from agent.logs.events import LogLevel


class JobResolver(CharacterBase):
    job: CharacterJob = Fighter

    spells: list[AttackSpellAction | SupportSpellAction] = []
    abilities: list[Action] = []

    def change_job(self, job: CharacterJob) -> None:
        self.spells = []
        self.abilities = []
        self.job = job

        self.apply_job_features()

    def apply_job_features(self) -> None:
        """Register class features based on current level."""
        # TODO: The primary stat should depend on the type of class (fighter should not use STR)
        self.attributes.spellcasting_stat = self.job.primary_stat
        self.attributes.save_proficiencies = self.job.save_proficiencies

        for feature in self.job.get_features_for_level(self.level):
            self._apply_job_feature(feature)

        for spell in self.job.get_spells_for_level(self.level):
            self._apply_spell(spell)

    def _apply_job_feature(self, feature: JobFeature) -> None:
        if feature.type == FeatureType.ACTIVE:
            action = ActionRegistry.create(
                id_=feature.ref_id,
                name=feature.name,
                description=feature.description,
                uses_per_rest=feature.uses_per_rest,
                **feature.kwargs,
            )
            self.abilities.append(action)
            self.log_event(f"{self.name} gained ability: {feature.name}", event_type=LogLevel.DETAIL)

        elif feature.type == FeatureType.PASSIVE:
            trait = TraitRegistry.create(
                id_=feature.ref_id,
                source=feature.name,
                description=feature.description,
                **feature.kwargs,
            )
            trait.on_apply(self)
            self.log_event(f"{self.name} gained passive trait: {feature.name}", event_type=LogLevel.DETAIL)

    def _apply_spell(self, spell: Spell) -> None:
        action = ActionRegistry.create(id_=spell.ref_id, stat=self.attributes.spellcasting_stat, **spell.model_dump())
        if isinstance(action, (AttackSpellAction, SupportSpellAction)):
            self.spells.append(action)
            self.log_event(f"{self.name} gained spell: {action.name}", event_type=LogLevel.DETAIL)
