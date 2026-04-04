import math
from enum import Enum

from pydantic import BaseModel, Field

from agent.actions.base import ActionCategory, ActionType


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
    action_extensions: list[ActionExtension] = Field(default_factory=list)

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
            ActionType.ATTACK,
            ActionType.CAST_SPELL,
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
        if not self.can_use_bonus(action_type):
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


class CasterProgression(Enum):
    NONE = 0.0
    THIRD = 1 / 3
    HALF = 0.5
    FULL = 1.0
    PACT = "pact"


class SpellLevel(int, Enum):
    CANTRIP = 0
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4
    LEVEL_5 = 5
    LEVEL_6 = 6
    LEVEL_7 = 7
    LEVEL_8 = 8
    LEVEL_9 = 9


class SpellSlots(BaseModel):
    progression: CasterProgression = CasterProgression.NONE
    slots: dict[SpellLevel, int] = {}
    max_slots: dict[SpellLevel, int] = {}

    def __str__(self) -> str:
        parts = []
        for level in sorted(self.max_slots.keys(), key=lambda x: x.value):
            current = self.slots.get(level, 0)
            maximum = self.max_slots[level]
            if maximum:
                parts.append(f"Lv{level.value}: {current}/{maximum}")
        return " | ".join(parts) if parts else "No spell slots"

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

    def recompute(self, level: int) -> None:
        """Recalculate slots based on class progression and level."""
        if self.progression == CasterProgression.NONE:
            table = {}

        elif self.progression == CasterProgression.PACT:
            table = {lvl: self.get_pact_spell_slots(level, lvl) for lvl in SpellLevel if lvl != SpellLevel.CANTRIP}

        else:
            # Compute effective caster level (rounded down)
            effective_level = max(1, math.floor(level * self.progression.value))

            table = {lvl: self.get_spell_slots(effective_level, lvl) for lvl in SpellLevel if lvl != SpellLevel.CANTRIP}

        table = {lvl: slot for lvl, slot in table.items() if slot > 0}
        self.max_slots = table.copy()  # type: ignore[assignment]
        self.slots = table.copy()  # type: ignore[assignment]

    def get_spell_slots(self, char_lvl: int, spell_lvl: SpellLevel) -> int:
        # Spell slots recover on long rest.
        progression = {
            SpellLevel.LEVEL_1: [2, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
            SpellLevel.LEVEL_2: [0, 0, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            SpellLevel.LEVEL_3: [0, 0, 0, 0, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            SpellLevel.LEVEL_4: [0, 0, 0, 0, 0, 0, 1, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            SpellLevel.LEVEL_5: [0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3],
            SpellLevel.LEVEL_6: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2],
            SpellLevel.LEVEL_7: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 2],
            SpellLevel.LEVEL_8: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
            SpellLevel.LEVEL_9: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
        }
        return progression[spell_lvl][char_lvl - 1]

    def get_pact_spell_slots(self, char_lvl: int, spell_lvl: SpellLevel) -> int:
        # A Warlock (Pact magic) always has a small number of slots, and all of them are the same level.
        # When the Warlock levels up and their slot level increases, their old lower-level slots are replaced.
        # Spell slots recover on short rest.
        progression = {
            SpellLevel.LEVEL_1: [1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            SpellLevel.LEVEL_2: [0, 0, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            SpellLevel.LEVEL_3: [0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            SpellLevel.LEVEL_4: [0, 0, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            SpellLevel.LEVEL_5: [0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4],
        }
        if spell_lvl not in progression:
            return 0
        return progression[spell_lvl][char_lvl - 1]
