from pydantic import BaseModel

from agent.actions.base import ActionCategory, ActionType


class ActionExtension(BaseModel):
    """Represents temporary extra action granted by effects like Haste or Action Surge."""

    source: str
    category: ActionCategory
    allowed_actions: list[ActionType] | None = None
    requires_previous_action: bool = False
    expires_end_of_turn: bool = True
