from typing import Any

from agent.actions.base import Action
from agent.models.enums import FeatureId


class ActionRegistry:
    """Registry for actions - supports classes, JSON paths, and direct instances.

    This allows:
    1. Legacy Python classes (for complex logic)
    2. JSON file paths (for testing/development)
    3. Pre-built Action instances (for DM dynamic generation)
    """

    _registry: dict[FeatureId, type[Action] | str | Action] = {}

    @classmethod
    def register(cls, id_: FeatureId, action: type[Action] | str | Action) -> None:
        """Register an action class, JSON path, or action instance.

        Args:
            id_: The feature ID
            action: Can be:
                - A Python class (legacy)
                - A string path to JSON (testing)
                - An Action instance (DM dynamic generation)
        """
        cls._registry[id_] = action

    @classmethod
    def create(cls, id_: FeatureId, **kwargs: Any) -> Action:
        """Create action instance from registry.

        Returns:
            Action instance ready to use
        """
        registered = cls._registry[id_]

        if isinstance(registered, str):
            # It's a JSON path - load composable action (for testing)
            from pathlib import Path

            from agent.actions.composable import ComposableAction

            json_path = Path(registered)
            with json_path.open() as f:
                action = ComposableAction.model_validate_json(f.read())
            # Override kwargs if provided (for dynamic customization)
            for key, value in kwargs.items():
                if hasattr(action, key):
                    setattr(action, key, value)
            return action
        if isinstance(registered, type):
            # It's a class - instantiate normally (legacy)
            return registered(id=id_.value, **kwargs)
        # It's already an Action instance (DM dynamic generation)
        # Return a copy to avoid shared state issues
        return registered.model_copy(deep=True)
