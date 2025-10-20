from agent.actions.base import Action
from agent.actions.common.spell import AttackSpellAction, SupportSpellAction
from agent.actions.registry import ActionRegistry
from agent.character.resolvers.base import CharacterBase
from agent.effects.registry import TraitRegistry
from agent.jobs.base import CharacterJob, JobFeature
from agent.jobs.feature import FeatureType
from agent.jobs.fighter import Fighter
from agent.logs.events import LogLevel


class JobResolver(CharacterBase):
    job: CharacterJob = Fighter

    spells: list[AttackSpellAction | SupportSpellAction] = []
    abilities: list[Action] = []

    def apply_job_features(self) -> None:
        """Register class features based on current level."""
        self.abilities = []
        for feature in self.job.get_features_for_level(self.level):
            self._apply_job_feature(feature)

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

        if feature.type == FeatureType.SPELL:
            spell = ActionRegistry.create(
                id_=feature.ref_id,
                name=feature.name,
                description=feature.description,
                stat=self.attributes.spellcasting_stat,
                **feature.kwargs,
            )
            if isinstance(spell, (AttackSpellAction, SupportSpellAction)):
                self.spells.append(spell)
                self.log_event(f"{self.name} gained spell: {feature.name}", event_type=LogLevel.DETAIL)

        elif feature.type == FeatureType.PASSIVE:
            trait = TraitRegistry.create(
                id_=feature.ref_id,
                source=feature.name,
                description=feature.description,
                **feature.kwargs,
            )
            trait.on_apply(self)
            self.log_event(f"{self.name} gained passive trait: {feature.name}", event_type=LogLevel.DETAIL)
