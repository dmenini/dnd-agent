import hashlib
import json
from collections.abc import Callable
from typing import Any, Literal

from anthropic import BaseModel

from agent.character.modifier import Modifier
from agent.effects.condition import Condition
from agent.models.enums import EventType, FeatureId

EFFECT_REGISTRY: dict[str, Callable] = {}


def register_effect(name: str | None = None) -> Callable:
    """Decorator to register an effect function."""

    def decorator(func: Callable) -> Callable:
        effect_name = name or func.__name__.replace("_effect", "")
        EFFECT_REGISTRY[effect_name] = func
        return func

    return decorator


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
    effect_type: str = ""  # Maps to an effect function
    effect_params: dict[str, Any] = {}  # Parameters passed to the effect
    conditions: list[Condition] = []

    def model_post_init(self, _: Any) -> None:
        if not self.name:
            self.name = self.feature_id.value.replace("_", " ").title()
        if not self.effect_type:
            self.effect_type = self.feature_id.value

        self.source_id = normalize_id(self.source_id)

    @property
    def id(self) -> str:
        data = self.model_dump(exclude={"id"}, mode="json")
        serialized = json.dumps(data, sort_keys=True)
        hash_part = hashlib.sha256(serialized.encode()).hexdigest()[:8]
        return f"{self.source_id}-{normalize_id(self.name)}-{hash_part}"

    def condition(self, target: Any) -> bool:
        if not self.conditions:
            return True
        return all(c.evaluate(target) for c in self.conditions)

    def condition_depends_on(self, field_name: str) -> bool:
        return any(field_name in c.depends_on_fields() for c in self.conditions)

    def apply(self, *args: Any, **kwargs: Any) -> None:
        """Apply this trait's effect by calling the registered effect function."""
        # Get the effect function from the registry
        effect_func = EFFECT_REGISTRY.get(self.effect_type)
        if not effect_func:
            msg = f"Unknown effect type: {self.effect_type}"
            raise ValueError(msg)

        # Call the effect function with stored parameters plus runtime args/kwargs
        effect_func(*args, **kwargs, **self.effect_params)


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
