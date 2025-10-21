from typing import Any

from agent.effects.base import Trait
from agent.jobs.feature import FeatureId


class TraitRegistry:
    _registry: dict[FeatureId, type[Trait]] = {}

    @classmethod
    def register(cls, id_: FeatureId, action_cls: type[Trait]) -> None:
        cls._registry[id_] = action_cls

    @classmethod
    def create(cls, id_: FeatureId, **kwargs: Any) -> Trait:
        return cls._registry[id_](**kwargs)
