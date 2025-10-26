import uuid
from collections.abc import Callable
from typing import Any, Literal

from anthropic import BaseModel
from pydantic import PrivateAttr, computed_field

from agent.character.modifier import Modifier
from agent.effects.trait_effects.support import apply_modifier
from agent.models.constants import EventType
from agent.models.enums import FeatureId


class Priority:
    HIGH: int = -100  # Execute first
    MEDIUM: int = 0
    LOW: int = 100  # Execute last


class TraitEffect(BaseModel):
    """Event listener to register dynamically."""

    event_type: EventType
    callback: Callable
    source_id: str
    priority: int = Priority.MEDIUM
    dependencies: list[str] = []

    def condition_depends_on(self, field_name: str) -> bool:
        return field_name in self.dependencies


class Trait(BaseModel):
    feature_id: FeatureId
    source_id: str
    name: str = ""
    description: str = ""
    _id: str = PrivateAttr(default_factory=lambda: str(uuid.uuid4()))
    _priority: int = PrivateAttr(default=Priority.MEDIUM)

    def model_post_init(self, _: Any) -> None:
        if not self.name:
            self.name = self.__class__.__name__
        if not self.description:
            self.description = self.__class__.__doc__ or ""

        self.source_id = normalize_id(self.source_id)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def id(self) -> str:
        return f"{self.source_id}-{normalize_id(self.name)}"

    def get_effect(self) -> TraitEffect:
        """Return a Modifier or Event effect to apply."""
        raise NotImplementedError

    def _make_event_effect(self, event_type: EventType, callback: Callable[..., None]) -> TraitEffect:
        return TraitEffect(source_id=self.id, event_type=event_type, callback=callback, priority=self._priority)

    def _make_modifier(self, attr: str, value: Any, op: Literal["set", "add", "mul"]) -> TraitEffect:
        mod = Modifier(source_id=self.id, attribute=attr, value=value, operation=op)
        return self._make_event_effect(event_type=EventType.MODIFIER, callback=lambda t: apply_modifier(t, mod))


def normalize_id(name: str) -> str:
    return name.replace(" ", "-").lower()
