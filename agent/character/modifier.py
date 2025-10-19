import builtins
from typing import Any, Literal

from pydantic import BaseModel, PrivateAttr


class Modifier(BaseModel):
    source_id: str
    attribute: str
    value: Any
    operation: Literal["set", "add", "mul"] = "set"


class ModifierRegistry(BaseModel):
    _modifiers: dict[str, list[Modifier]] = PrivateAttr(default_factory=dict)
    _stacking_rules: dict[str, Literal["sum", "min", "max"]] = PrivateAttr(default_factory=dict)

    def add(self, modifier: Modifier, stacking_rule: Literal["sum", "min", "max"] = "sum") -> None:
        attr = modifier.attribute
        if attr not in self._modifiers:
            self._modifiers[attr] = []
            self._stacking_rules[attr] = stacking_rule
        self._modifiers[attr].append(modifier)

    def remove(self, source_id: str) -> Modifier | None:
        for attr, mods in list(self._modifiers.items()):
            for i, m in enumerate(mods):
                if m.source_id == source_id:
                    # Pop the modifier from the list
                    removed = mods.pop(i)

                    # Clean up empty modifier lists
                    if not mods:
                        del self._modifiers[attr]
                        self._stacking_rules.pop(attr, None)

                    return removed

        return None

    def get(self, attr: str) -> list[Modifier]:
        return self._modifiers.get(attr, [])

    def attributes(self) -> list[str]:
        """Return all attributes currently affected by modifiers."""
        return list(self._modifiers.keys())

    def stack(self, attr: str, op: Literal["set", "add", "mul"]) -> Any:
        """
        Select a final modifier value for the given attribute and operation based on the configured stacking rule.
        """
        neutral_el = 1 if op == "mul" else 0
        mods = self._modifiers.get(attr, [])
        if not mods:
            return neutral_el

        if op == "set":
            # Most recent 'set' overrides previous ones
            for mod in reversed(mods):
                if mod.operation == op:
                    return mod.value
            return None

        stacking_rule = self._stacking_rules[attr]
        mode_fn = getattr(builtins, stacking_rule)
        return mode_fn(mod.value for mod in mods if mod.operation == op) or neutral_el
