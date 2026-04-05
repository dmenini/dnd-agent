from typing import Any

from agent.actions.base import Action
from agent.models.enums import FeatureId


class ActionRegistry:
    _registry: dict[FeatureId, type[Action] | str] = {}  # Can be class or JSON path

    @classmethod
    def register(cls, id_: FeatureId, action_cls: type[Action] | str) -> None:
        """Register an action class or JSON path."""
        cls._registry[id_] = action_cls

    @classmethod
    def create(cls, id_: FeatureId, **kwargs: Any) -> Action:
        """Create action instance from class or JSON definition."""
        registered = cls._registry[id_]

        if isinstance(registered, str):
            # It's a JSON path - load composable action
            from agent.actions.loader import ActionLoader  # noqa: PLC0415

            action = ActionLoader.from_file(registered)
            # Override kwargs if provided (for dynamic customization)
            for key, value in kwargs.items():
                if hasattr(action, key):
                    setattr(action, key, value)
            return action
        else:
            # It's a class - instantiate normally
            return registered(id=id_.value, **kwargs)
