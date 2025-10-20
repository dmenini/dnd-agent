from typing import Any

from agent.actions.base import Action


class ActionRegistry:
    _registry: dict[str, type[Action]] = {}

    @classmethod
    def register(cls, id_: str, action_cls: type[Action]) -> None:
        cls._registry[id_] = action_cls

    @classmethod
    def create(cls, id_: str, **kwargs: Any) -> Action:
        return cls._registry[id_](id=id_, **kwargs)
