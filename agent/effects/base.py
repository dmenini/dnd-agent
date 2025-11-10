import hashlib
import json
from typing import Any, Literal

from anthropic import BaseModel

from agent.character.modifier import Modifier
from agent.models.enums import EventType, FeatureId


class Priority:
    HIGH: int = -100  # Execute first
    MEDIUM: int = 0
    LOW: int = 100  # Execute last


class Trait(BaseModel):
    feature_id: FeatureId
    source_id: str
    name: str = ""
    description: str = ""
    priority: int = Priority.MEDIUM
    event_type: EventType

    def model_post_init(self, _: Any) -> None:
        if not self.name:
            self.name = self.__class__.__name__
        if not self.description:
            self.description = self.__class__.__doc__ or ""

        self.source_id = normalize_id(self.source_id)

    @property
    def id(self) -> str:
        data = self.model_dump(exclude={"id"}, mode="json")
        serialized = json.dumps(data, sort_keys=True)
        hash_part = hashlib.sha256(serialized.encode()).hexdigest()[:8]
        return f"{self.source_id}-{normalize_id(self.name)}-{hash_part}"

    def condition(self, target: Any) -> bool:  # noqa: ARG002
        """Check if this trait's effect should be applied."""
        return True

    def apply(self, *args: Any, **kwargs: Any) -> None:
        """Apply this trait's effect to the target."""
        raise NotImplementedError

    def condition_depends_on(self, field_name: str) -> bool:  # noqa: ARG002
        """Whether this trait's condition depends on a specific field."""
        return False


class ModifierTrait(Trait):
    """Trait that modifies a character attribute."""

    event_type: EventType = EventType.MODIFIER
    attribute: str
    value: Any
    operation: Literal["set", "add", "mul"] = "add"

    def apply(self, target: Any) -> None:
        if self.condition(target):
            modifier = Modifier(source_id=self.id, attribute=self.attribute, value=self.value, operation=self.operation)
            target.attributes.add_modifier(modifier)


def normalize_id(name: str) -> str:
    return name.replace(" ", "-").lower()
