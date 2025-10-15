from enum import Enum

from pydantic import BaseModel, Field


class SpellLevel(Enum):
    CANTRIP = 0
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3


class ActionEconomy(BaseModel):
    standard_actions: int = 1
    max_standard_actions: int = 1
    bonus_actions: int = 1
    max_bonus_actions: int = 1
    reaction_available: bool = True
    movement_available: bool = True

    def restore_all(self) -> None:
        """Restore all resources. Must be done after each round."""
        self.standard_actions = self.max_standard_actions
        self.bonus_actions = self.max_bonus_actions
        self.movement_available = True
        self.reaction_available = True


class SpellSlots(BaseModel):
    slots: dict[SpellLevel, int] = Field(
        default_factory=lambda: {
            SpellLevel.LEVEL_1: 2,
            SpellLevel.LEVEL_2: 0,
            SpellLevel.LEVEL_3: 0,
        }
    )  # default low-level caster
    max_slots: dict[SpellLevel, int] = Field(
        default_factory=lambda: {
            SpellLevel.LEVEL_1: 2,
            SpellLevel.LEVEL_2: 0,
            SpellLevel.LEVEL_3: 0,
        }
    )

    def has_slot(self, level: SpellLevel) -> bool:
        """Check if there are slots left for the given spell level. Cantrips are always available."""
        if level == SpellLevel.CANTRIP:
            return True
        return self.slots.get(level, 0) > 0

    def consume(self, level: SpellLevel) -> None:
        if not self.has_slot(level):
            msg = f"No spell slots remaining for level {level}"
            raise ValueError(msg)

        if level != SpellLevel.CANTRIP:
            self.slots[level] -= 1

    def restore_all(self) -> None:
        """Restore all resources. Must be done after combat ends."""
        self.slots = self.max_slots.copy()
