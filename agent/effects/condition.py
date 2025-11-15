import re
from typing import Any, Literal

from pydantic import BaseModel, field_validator


class Condition(BaseModel):
    """Base condition that can be evaluated."""

    def evaluate(self, target: Any) -> bool:
        raise NotImplementedError

    def depends_on_fields(self) -> set[str]:
        """Return fields this condition depends on."""
        return set()


class FieldCondition(Condition):
    """Check a field value, supports nested paths like 'armor.armor_type'."""

    field: str  # Can be "armor" or "armor.armor_type" or "stats.strength"
    operator: Literal[
        "eq",
        "ne",
        "gt",
        "gte",
        "lt",
        "lte",
        "in",
        "not_in",
        "contains",
        "not_contains",
        "bool",
        "not_bool",
        "is_none",
        "is_not_none",
        "startswith",
        "endswith",
        "matches",
    ]
    value: Any = None

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: Any, info: Any) -> Any:
        """Validate that value is provided when needed."""
        operator = info.data.get("operator")
        no_value_operators = {"bool", "not_bool", "is_none", "is_not_none"}

        if operator not in no_value_operators and v is None:
            msg = f"Operator '{operator}' requires a value"
            raise ValueError(msg)

        return v

    def _get_nested_value(self, target: Any) -> tuple[Any, bool]:
        """Get value from potentially nested field path.

        Returns (value, exists) tuple where exists indicates if path was valid.
        """
        path_parts = self.field.split(".")
        obj = target

        for part in path_parts:
            if not hasattr(obj, part):
                return None, False
            obj = getattr(obj, part)
            if obj is None:
                return None, True  # Path exists but value is None

        return obj, True

    def evaluate(self, target: Any) -> bool:  # noqa: PLR0912, C901
        field_value, exists = self._get_nested_value(target)

        # Handle non-existent paths
        if not exists:
            return self.operator in {"not_bool", "is_none"}

        match self.operator:
            case "bool":
                res = bool(field_value)
            case "not_bool":
                res = not bool(field_value)
            case "is_none":
                res = field_value is None
            case "is_not_none":
                res = field_value is not None
            case "eq":
                res = field_value == self.value
            case "ne":
                res = field_value != self.value
            case "gt":
                res = field_value > self.value
            case "gte":
                res = field_value >= self.value
            case "lt":
                res = field_value < self.value
            case "lte":
                res = field_value <= self.value
            case "in":
                res = field_value in self.value
            case "not_in":
                res = field_value not in self.value
            case "contains":
                # Check if field_value contains self.value
                # Works for strings, lists, sets, dicts, etc.
                res = self.value in field_value
            case "not_contains":
                res = self.value not in field_value
            case "startswith":
                res = str(field_value).startswith(str(self.value))
            case "endswith":
                res = str(field_value).endswith(str(self.value))
            case "matches":
                # Simple pattern matching with * wildcard
                pattern = str(self.value).replace("*", ".*")
                res = bool(re.match(f"^{pattern}$", str(field_value)))
            case _:
                msg = f"Unknown operator: {self.operator}"
                raise ValueError(msg)
        return res

    def depends_on_fields(self) -> set[str]:
        # Return the root field (first part of the path)
        return {self.field.split(".")[0]}


class CompositeCondition(Condition):
    """Combine multiple conditions with logical operators."""

    operator: Literal["and", "or", "not"]
    conditions: list[Condition]

    @field_validator("conditions")
    @classmethod
    def validate_conditions(cls, v: list[Condition], info: Any) -> list[Condition]:
        """Validate that conditions list is appropriate for operator."""
        operator = info.data.get("operator")

        if operator == "not" and len(v) != 1:
            raise ValueError("'not' operator requires exactly one condition")

        if operator in {"and", "or"} and len(v) < 1:
            msg = f"'{operator}' operator requires at least one condition"
            raise ValueError(msg)

        return v

    def evaluate(self, target: Any) -> bool:
        match self.operator:
            case "and":
                return all(c.evaluate(target) for c in self.conditions)

            case "or":
                return any(c.evaluate(target) for c in self.conditions)

            case "not":
                return not self.conditions[0].evaluate(target)

            case _:
                msg = f"Unknown operator: {self.operator}"
                raise ValueError(msg)

    def depends_on_fields(self) -> set[str]:
        return set().union(*(c.depends_on_fields() for c in self.conditions))


class When:
    """Builder for creating conditions with a fluent interface."""

    @staticmethod
    def field(field: str) -> "FieldBuilder":
        return FieldBuilder(field)

    @staticmethod
    def all(*conditions: Condition) -> CompositeCondition:
        return CompositeCondition(operator="and", conditions=list(conditions))

    @staticmethod
    def any(*conditions: Condition) -> CompositeCondition:
        return CompositeCondition(operator="or", conditions=list(conditions))

    @staticmethod
    def not_(condition: Condition) -> CompositeCondition:
        return CompositeCondition(operator="not", conditions=[condition])


class FieldBuilder:
    """Fluent builder for field conditions."""

    def __init__(self, field: str) -> None:
        self.field = field

    def exists(self) -> FieldCondition:
        return FieldCondition(field=self.field, operator="bool")

    def is_truthy(self) -> FieldCondition:
        return FieldCondition(field=self.field, operator="bool")

    def is_falsy(self) -> FieldCondition:
        return FieldCondition(field=self.field, operator="not_bool")

    def is_none(self) -> FieldCondition:
        return FieldCondition(field=self.field, operator="is_none")

    def is_not_none(self) -> FieldCondition:
        return FieldCondition(field=self.field, operator="is_not_none")

    def equals(self, value: Any) -> FieldCondition:
        return FieldCondition(field=self.field, operator="eq", value=value)

    def not_equals(self, value: Any) -> FieldCondition:
        return FieldCondition(field=self.field, operator="ne", value=value)

    def greater_than(self, value: Any) -> FieldCondition:
        return FieldCondition(field=self.field, operator="gt", value=value)

    def greater_or_equal(self, value: Any) -> FieldCondition:
        return FieldCondition(field=self.field, operator="gte", value=value)

    def less_than(self, value: Any) -> FieldCondition:
        return FieldCondition(field=self.field, operator="lt", value=value)

    def less_or_equal(self, value: Any) -> FieldCondition:
        return FieldCondition(field=self.field, operator="lte", value=value)

    def is_in(self, value: list | set | tuple) -> FieldCondition:
        return FieldCondition(field=self.field, operator="in", value=value)

    def not_in(self, value: list | set | tuple) -> FieldCondition:
        return FieldCondition(field=self.field, operator="not_in", value=value)

    def contains(self, value: Any) -> FieldCondition:
        return FieldCondition(field=self.field, operator="contains", value=value)

    def not_contains(self, value: Any) -> FieldCondition:
        return FieldCondition(field=self.field, operator="not_contains", value=value)

    def startswith(self, value: str) -> FieldCondition:
        return FieldCondition(field=self.field, operator="startswith", value=value)

    def endswith(self, value: str) -> FieldCondition:
        return FieldCondition(field=self.field, operator="endswith", value=value)

    def matches(self, pattern: str) -> FieldCondition:
        return FieldCondition(field=self.field, operator="matches", value=pattern)
