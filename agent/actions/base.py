from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from agent.models.enums import TargetingType

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.character.resources import ActionEconomy
    from agent.models.context import CombatContext

"""
| Category        | Frequency                    | When usable                                                 |
| --------------- | ---------------------------- | ----------------------------------------------------------- |
| Movement        | once per turn (can be split) | During your turn                                            |
| Standard Action | once per turn                | During your turn                                            |
| Bonus Action    | once per turn                | During your turn, only if you have something that grants it |
| Reaction        | at most once per round       | When triggered (can be during another creature's turn)      |

| Action Type  | Description                                 | Notes                                 |
| ------------ | ------------------------------------------- | ------------------------------------- |
| Attack       | Make one or more weapon attacks             | Replaced by *Extra Attack* feature    |
| Cast a Spell | Cast any spell with a 1-action casting time | Can't also cast a leveled bonus spell |
| Dash         | Move extra distance equal to your speed     | No attack                             |
| Disengage    | Avoid opportunity attacks                   | Defensive                             |
| Dodge        | Gain disadvantage to attackers              | Defensive                             |
| Help         | Give advantage to ally                      | Utility                               |
| Hide         | Attempt to become unseen                    | Requires cover                        |
| Ready        | Prepare an action + reaction trigger        | Uses reaction later                   |
| Search       | Look for something specific                 | DM discretion                         |
| Use Object   | Interact with complex objects               | Usually free once                     |
"""


class ActionCategory(str, Enum):
    STANDARD = "standard"
    BONUS = "bonus"
    REACTION = "reaction"
    MOVEMENT = "movement"


class ActionType(str, Enum):
    ATTACK = "attack"
    CAST_SPELL = "cast_spell"
    USE_OBJECT = "use_object"
    DASH = "dash"
    MOVE = "move"
    DODGE = "dodge"
    WAIT = "pass"
    DISENGAGE = "disengage"
    HELP = "help"
    HIDE = "hide"
    OFF_HAND_ATTACK = "off_attack"  # bonus
    SPECIAL = "special"  # bonus


class Action(BaseModel, ABC):
    """Action resolved from Agent decision"""

    id: str
    name: str
    description: str
    action_type: ActionType
    category: ActionCategory
    targeting: TargetingType
    hits: int = 1
    range: float = 0

    @abstractmethod
    def is_available(self, action_economy: ActionEconomy) -> bool:
        raise NotImplementedError

    @abstractmethod
    def execute(self, actor: Character, target: Any, ctx: CombatContext) -> None:
        raise NotImplementedError

    @abstractmethod
    def finalize(self, actor: Character) -> None:
        raise NotImplementedError


class StandardAction(Action, ABC):
    category: ActionCategory = ActionCategory.STANDARD
    breaks_stealth: bool = True

    def is_available(self, action_economy: ActionEconomy) -> bool:
        return action_economy.can_use_standard(self.action_type)

    def finalize(self, actor: Character) -> None:
        """Consume resources (action point by default)."""
        actor.action_economy.use_standard(self.action_type)
        if self.breaks_stealth and actor.is_hidden:
            actor.unhide()


class BonusAction(Action, ABC):
    category: ActionCategory = ActionCategory.BONUS
    breaks_stealth: bool = True

    def is_available(self, action_economy: ActionEconomy) -> bool:
        return action_economy.can_use_bonus(self.action_type)

    def finalize(self, actor: Character) -> None:
        """Consume resources (action point by default)."""
        actor.action_economy.use_bonus(self.action_type)
        if self.breaks_stealth and actor.is_hidden:
            actor.unhide()


class LimitedBonusAction(BonusAction, ABC):
    category: ActionCategory = ActionCategory.BONUS
    uses_per_rest: int = 1

    _current_uses: int = 0

    def is_available(self, action_economy: ActionEconomy) -> bool:
        use_available = self._current_uses < self.uses_per_rest
        return use_available and super().is_available(action_economy)

    def _consume_use(self) -> None:
        if self._current_uses >= self.uses_per_rest:
            raise ValueError
        self._current_uses += 1

    def finalize(self, actor: Character) -> None:
        super().finalize(actor)
        self._consume_use()

    def rest(self) -> None:
        self._current_uses = 0
