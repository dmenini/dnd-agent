from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from agent.character.resources import ActionEconomy

if TYPE_CHECKING:
    from agent.character.character import Character


class ActionCategory(str, Enum):
    STANDARD = "standard"
    BONUS = "bonus"
    REACTION = "reaction"
    MOVEMENT = "movement"


class ActionType(str, Enum):
    MAIN_HAND_ATTACK = "main_attack"
    OFF_HAND_ATTACK = "off_attack"
    RANGED_ATTACK = "ranged_attack"
    SPELL = "spell"
    UTILITY = "utility"
    SPECIAL = "special"
    DASH = "dash"
    MOVE = "move"
    DODGE = "dodge"
    WAIT = "pass"


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
