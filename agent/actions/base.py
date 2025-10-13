from __future__ import annotations

from typing import Any, TYPE_CHECKING

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
        """Consume resources (action point by default)."""
        if actor.action_economy.standard_actions <= 0:
            raise ValueError("No standard actions left")
        actor.action_economy.standard_actions -= 1
