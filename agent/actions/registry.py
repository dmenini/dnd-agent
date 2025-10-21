from typing import Any

from agent.actions.base import Action
from agent.jobs.feature import FeatureId


class ActionRegistry:
    _registry: dict[FeatureId, type[Action]] = {}

    @classmethod
    def register(cls, id_: FeatureId, action_cls: type[Action]) -> None:
        cls._registry[id_] = action_cls

    @classmethod
    def create(cls, id_: FeatureId, **kwargs: Any) -> Action:
        return cls._registry[id_](id=id_.value, **kwargs)
