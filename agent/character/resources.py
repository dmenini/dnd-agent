from enum import Enum

from pydantic import BaseModel, Field

from agent.actions.base import ActionCategory, ActionType


class SpellLevel(Enum):
    CANTRIP = "0"
    LEVEL_1 = "1"
    LEVEL_2 = "2"
    LEVEL_3 = "3"


class ActionExtension(BaseModel):
    """Represents temporary extra action granted by effects like Haste or Action Surge."""

    source: str
    category: ActionCategory
    allowed_actions: list[ActionType] | None = None
    requires_previous_action: bool = False
    expires_end_of_turn: bool = True


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

    # Temporary rule extensions
    can_act: bool = True
    action_extensions: list[ActionExtension] = []

    def restore_turn(self) -> None:
        """Restore per-turn actions and movement (start of your turn)."""
        self.standard_actions = self.max_standard_actions
        self.bonus_actions = self.max_bonus_actions
        self.movement_used = 0.0
        self.movement_available = True
        self.last_standard_action = None
        self.last_bonus_action = None
        self.action_extensions = [e for e in self.action_extensions if not e.expires_end_of_turn]
        self.can_act = True

    def restore_reaction(self) -> None:
        """Restore reaction (start of your next turn)."""
        self.reaction_available = True
        self.reaction_trigger = None

    def can_use_standard(self, action_type: ActionType | None = None) -> bool:
        """Determine if a standard action can be taken, considering extensions."""
        if not self.can_act:
            return False

        base_allowed = [
            ActionType.ATTACK,
            ActionType.CAST_SPELL,
            ActionType.DASH,
            ActionType.DODGE,
            ActionType.HIDE,
            ActionType.USE_OBJECT,
        ]

        # Check normal rules
        if action_type in (None, *base_allowed) and self.standard_actions > 0:
            return True

        # Check if an extension grants this action
        for ext in self.action_extensions:
            if ext.category != ActionCategory.STANDARD:
                continue

            if ext.requires_previous_action and not self.last_standard_action:
                # e.g. Haste requires the first standard action to be used
                continue

            if ext.allowed_actions is None or action_type in ext.allowed_actions:
                return True

        return False

    def use_standard(self, action_type: ActionType | None = None) -> bool:
        """Consume a standard or extended action if allowed."""
        if not self.can_use_standard(action_type):
            return False

        if self.standard_actions > 0:
            self.standard_actions -= 1
        else:
            # Consumed via an extension, so we remove it once used
            self.remove_extension(category=ActionCategory.STANDARD, types=action_type)

        self.last_standard_action = action_type
        return True

    def can_use_bonus(self, action_type: ActionType | None = None) -> bool:
        if not self.can_act:
            return False

        base_allowed = [
            ActionType.OFF_HAND_ATTACK,
            ActionType.SPECIAL,
        ]

        # Check normal rules
        if action_type in (None, *base_allowed) and self.bonus_actions > 0:
            return True

        # Check if an extension grants this action
        for ext in self.action_extensions:
            if ext.category != ActionCategory.BONUS:
                continue

            if ext.requires_previous_action and not self.last_bonus_action:
                continue

            if ext.allowed_actions is None or action_type in ext.allowed_actions:
                return True

        return False

    def use_bonus(self, action_type: ActionType | None = None) -> bool:
        if self.can_use_bonus(action_type):
            return False

        if self.bonus_actions > 0:
            self.bonus_actions -= 1
        else:
            # Consumed via an extension, so we remove it once used
            self.remove_extension(category=ActionCategory.BONUS, types=action_type)

        self.last_bonus_action = action_type
        return True

    def remove_extension(self, category: ActionCategory, types: ActionType | None) -> None:
        for ext in list(self.action_extensions):
            if ext.category == category and (ext.allowed_actions is None or types in ext.allowed_actions):
                self.action_extensions.remove(ext)
                return

    def can_use_reaction(self) -> bool:
        if not self.can_act:
            return False

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
        # However, if the AI simply turns, we don't want to burn the movement
        if distance > 0:
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

    def __str__(self) -> str:
        slots = []
        for level in self.slots:
            slot_str = f"Level {level.value}: {self.slots[level]}/{self.max_slots[level]}"
            slots.append(slot_str)
        return " | ".join(slots)

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
