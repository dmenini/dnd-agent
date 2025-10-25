from typing import Any

from agent.effects.base import Trait
from agent.models.enums import FeatureId


class TraitRegistry:
    _registry: dict[FeatureId, type[Trait]] = {}

    @classmethod
    def register(cls, feature_id: FeatureId, action_cls: type[Trait]) -> None:
        cls._registry[feature_id] = action_cls

    @classmethod
    def create(cls, feature_id: FeatureId, source_id: str, **kwargs: Any) -> Trait:
        return cls._registry[feature_id](feature=feature_id, source_id=source_id, **kwargs)
