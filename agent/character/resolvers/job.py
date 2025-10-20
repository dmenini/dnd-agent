from agent.actions.base import Action
from agent.actions.registry import ActionRegistry
from agent.character.resolvers.base import CharacterBase
from agent.equipment.spells import Spell
from agent.jobs.base import CharacterJob, FeatureType, JobFeature
from agent.jobs.fighter import Fighter
from agent.logs.events import EventType


class JobResolver(CharacterBase):
    job: CharacterJob = Fighter

    spells: list[Spell] = []
    abilities: list[Action] = []

    def apply_job_features(self) -> None:
        """Register class features based on current level."""
        self.abilities = []
        for feature in self.job.get_features_for_level(self.level):
            self._apply_job_feature(feature)

    def _apply_job_feature(self, feature: JobFeature) -> None:
        if feature.type == FeatureType.ACTIVE:
            action = ActionRegistry.create(
                id_=feature.reference_id,
                name=feature.name,
                description=feature.description,
            )
            self.abilities.append(action)
            self.log_event(f"{self.name} gained ability: {feature.name}", event_type=EventType.DETAIL)
