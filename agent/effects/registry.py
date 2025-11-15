from collections.abc import Callable
from typing import Any

from agent.models.enums import FeatureId


class TraitRegistry:
    """Registry that maps feature IDs to builder functions."""

    _registry: dict[FeatureId, Callable[..., Any]] = {}

    @classmethod
    def register(cls, feature_id: FeatureId, builder: Callable) -> None:
        """Register a builder function for a feature ID."""
        cls._registry[feature_id] = builder

    @classmethod
    def create(cls, feature_id: FeatureId, source_id: str, **kwargs: Any) -> Any:
        """Create a trait instance using the registered builder."""
        if feature_id not in cls._registry:
            msg = f"Feature ID '{feature_id}' is not registered"
            raise ValueError(msg)

        builder = cls._registry[feature_id]
        return builder(source_id=source_id, **kwargs)

    @classmethod
    def list_all(cls) -> list[FeatureId]:
        """Get a list of all registered feature IDs."""
        return list(cls._registry.keys())

    @classmethod
    def is_registered(cls, feature_id: FeatureId) -> bool:
        """Check if a feature ID is registered."""
        return feature_id in cls._registry
