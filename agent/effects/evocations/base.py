from pydantic import BaseModel, Field

from agent.actions.base import Action
from agent.character.resources import ActionEconomy
from agent.jobs.feature import JobFeature
from agent.models.enums import FeatureId
from agent.models.position import Position


class Evocation(BaseModel):
    source_id: str
    name: str
    duration: int
    position: Position | None = None
    features: list[JobFeature] = Field(default_factory=list)
    on_cast_use: FeatureId | None = None
    action_economy: ActionEconomy = Field(default_factory=ActionEconomy)

    def available_actions(self) -> list[Action]:
        # Lazy import to avoid circular dependency
        from agent.actions.common.evocation import RepositionEvocationAction  # noqa: PLC0415

        actions = []

        # All evocations have repositioning (like characters have movement)
        reposition = RepositionEvocationAction(
            id=self.source_id + "-" + FeatureId.REPOSITION_EVOCATION.value,
            name=f"Move {self.name}",
            description=f"Move the {self.name} up to 20 feet.",
            evocation_name=self.name,
            range=20,
        )
        if reposition.is_available(self.action_economy):
            actions.append(reposition)

        # Add feature-specific actions (attacks, etc.)
        for feature in self.features:
            action = feature.to_action()
            action.id = self.source_id + "-" + feature.ref_id.value
            if action.is_available(self.action_economy):
                actions.append(action)
        return actions

    def is_expired(self) -> bool:
        return self.duration <= 0
