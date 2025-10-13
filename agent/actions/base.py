from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from agent.models.enums import ActionCategory, ActionType

if TYPE_CHECKING:
    from agent.models.character import Character


class ActionEconomy(BaseModel):
    standard_actions: int = 1
    max_standard_actions: int = 1
    bonus_actions: int = 1
    max_bonus_actions: int = 1
    reaction_available: bool = True
    movement_available: bool = True

    def consume(self, category: ActionCategory) -> None:
        """Consume the resources used by the action."""
        if category == ActionCategory.STANDARD:
            if self.standard_actions <= 0:
                raise ValueError("No standard actions left")
            self.standard_actions -= 1
        elif category == ActionCategory.BONUS:
            if self.bonus_actions <= 0:
                raise ValueError("No bonus actions left")
            self.bonus_actions -= 1
        elif category == ActionCategory.REACTION:
            if not self.reaction_available:
                raise ValueError("Reaction already used")
            self.reaction_available = False
        elif category == ActionCategory.MOVEMENT:
            if not self.movement_available:
                raise ValueError("Already moved")
            self.movement_available = False

    def restore_all(self) -> None:
        """Restore all resources. Must be done after each round."""
        self.standard_actions = self.max_standard_actions
        self.bonus_actions = self.max_bonus_actions
        self.movement_available = True
        self.reaction_available = True


class Action(BaseModel):
    """Action resolved from Agent decision"""

    id: str
    name: str
    description: str
    action_type: ActionType
    category: ActionCategory

    def is_available(self, action_economy: ActionEconomy) -> bool:
        return action_economy.standard_actions > 0

    def execute(self, actor: Character, target: Any) -> str:
        raise NotImplementedError

    def finalize(self, actor: Character) -> None:
        actor.action_economy.consume(self.category)
