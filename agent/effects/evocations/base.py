from pydantic import BaseModel

from agent.actions.base import Action
from agent.jobs.feature import JobFeature
from agent.models.enums import FeatureId
from agent.models.position import Position


class Evocation(BaseModel):
    source_id: str
    name: str
    duration: int
    position: Position | None = None
    features: list[JobFeature] = []
    on_cast_use: FeatureId | None = None

    def available_actions(self) -> list[Action]:
        actions = []
        for feature in self.features:
            actions.append(feature.to_action())
        return actions

    def is_expired(self) -> bool:
        return self.duration <= 0
