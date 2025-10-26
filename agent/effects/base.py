import uuid
from collections.abc import Callable
from typing import Any, Literal

from anthropic import BaseModel
from pydantic import PrivateAttr, computed_field

from agent.character.modifier import Modifier
from agent.models.constants import EventType
from agent.models.enums import FeatureId


class Priority:
    HIGH: int = -100  # Execute first
    MEDIUM: int = 0
    LOW: int = 100  # Execute last


class EventEffect(BaseModel):
    """Describes an event listener to register dynamically."""

    event_type: EventType
    callback: Callable
    source_id: str
    priority: int = Priority.MEDIUM


class TraitEffect(BaseModel):
    """An effect that only applies when its condition is true."""

    effect: Modifier | EventEffect
    condition: Callable[[Any], bool] = lambda t: True  # noqa: ARG005

    def should_apply(self, arg: Any) -> bool:
        return self.condition(arg)


class Trait(BaseModel):
    feature_id: FeatureId
    source_id: str
    name: str = ""
    description: str = ""
    _id: str = PrivateAttr(default=str(uuid.uuid4()))
    _priority: int = PrivateAttr(default=Priority.MEDIUM)

    def model_post_init(self, _: Any) -> None:
        if not self.name:
            self.name = self.__class__.__name__
        if not self.description:
            self.description = self.__class__.__doc__ or ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def id(self) -> str:
        return self._id

    def get_effect(self) -> TraitEffect:
        """Return a Modifier or Event effect to apply."""
        raise NotImplementedError

    def _make_event_effect(self, event_type: EventType, callback: Callable[..., None]) -> TraitEffect:
        return TraitEffect(
            effect=EventEffect(source_id=self._id, event_type=event_type, callback=callback, priority=self._priority)
        )

    def _make_modifier(self, attr: str, value: Any, op: Literal["set", "add", "mul"]) -> TraitEffect:
        return TraitEffect(effect=Modifier(source_id=self._id, attribute=attr, value=value, operation=op))
