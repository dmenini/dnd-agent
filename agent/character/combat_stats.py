"""Combat state component - transient combat-related data."""

from pydantic import BaseModel, Field

from agent.character.resources import ActionEconomy
from agent.models.position import Position


class CombatStats(BaseModel):
    """Transient combat state for a character.

    This separates combat-specific state from permanent character data,
    making it easy to reset between encounters or save/load character sheets.
    """

    pos: Position = Field(default_factory=lambda: Position(x=0, y=0))
    turn_done: bool = True
    action_economy: ActionEconomy = Field(default_factory=ActionEconomy)
    stealth_value: int = 0

    @property
    def is_hidden(self) -> bool:
        """Character is hidden if they have a stealth value."""
        return self.stealth_value > 0
