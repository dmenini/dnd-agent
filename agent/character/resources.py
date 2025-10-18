from enum import Enum

from pydantic import BaseModel, Field

from agent.actions.base import ActionType


class SpellLevel(Enum):
    CANTRIP = 0
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3


class ActionEconomy(BaseModel):
    # Core resources
    standard_actions: int = 1
    max_standard_actions: int = 1
    bonus_actions: int = 1
    max_bonus_actions: int = 1
    reaction_available: bool = True

    # Movement tracking
    movement_used: float = 0.0
    movement_available: bool = True

    # Tracking what actions were used
    last_standard_action: ActionType | None = None
    last_bonus_action: ActionType | None = None
    reaction_trigger: str | None = None

    def restore_turn(self) -> None:
        """Restore per-turn actions and movement (start of your turn)."""
        self.standard_actions = self.max_standard_actions
        self.bonus_actions = self.max_bonus_actions
        self.movement_used = 0.0
        self.movement_available = True
        self.last_standard_action = None
        self.last_bonus_action = None

    def restore_reaction(self) -> None:
        """Restore reaction (start of your next turn)."""
        self.reaction_available = True
        self.reaction_trigger = None

    def can_use_standard(self, action_type: ActionType | None = None) -> bool:
        if action_type is None or action_type in [
            ActionType.MAIN_HAND_ATTACK,
            ActionType.CAST_SPELL,
            ActionType.RANGED_ATTACK,
            ActionType.DASH,
            ActionType.DODGE,
            ActionType.USE_OBJECT,
        ]:
            return self.standard_actions > 0
        return False

    def use_standard(self, action_type: ActionType | None = None) -> None:
        if action_type and not self.can_use_standard(action_type):
            raise RuntimeError("No standard action remaining this turn.")
        self.standard_actions -= 1
        self.last_standard_action = action_type

    def can_use_bonus(self, action_type: ActionType | None = None) -> bool:
        if action_type is None or action_type in [
            ActionType.OFF_HAND_ATTACK,
        ]:
            return self.bonus_actions > 0
        return False

    def use_bonus(self, action_type: ActionType | None = None) -> None:
        if action_type and not self.can_use_bonus(action_type):
            raise RuntimeError("No bonus action remaining this turn.")
        self.bonus_actions -= 1
        self.last_bonus_action = action_type

    def can_use_reaction(self) -> bool:
        return self.reaction_available

    def use_reaction(self, trigger: str | None = None) -> None:
        if trigger and not self.reaction_available:
            raise RuntimeError("Reaction already used this round.")
        self.reaction_available = False
        self.reaction_trigger = trigger

    def can_move(self, distance: float, speed_available: float | None = None) -> bool:
        if speed_available is not None:
            return self.movement_available and self.movement_used + distance <= speed_available
        return self.movement_available

    def use_movement(self, distance: float) -> None:
        # The AI doesn't work well if we keep the movement as a float,
        # so after one movement action prevents it from using it again in the same turn
        self.movement_used += distance
        self.movement_available = False


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
