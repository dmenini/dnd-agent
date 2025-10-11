from enum import Enum
from typing import Literal

PartyType = Literal["players", "enemies", "neutrals"]


class TurnPhase(str, Enum):
    DECIDE = "decide"
    VERIFY = "verify"
    ROLL = "roll"
    EXECUTE = "execute"
    START = "start"
    END = "end"


class ActionType(str, Enum):
    ATTACK = "attack"
    SHOOT = "shoot"
    MOVE = "move"
    CAST_SPELL = "cast_spell"
    ROLEPLAY = "roleplay"
    WAIT = "wait"


COMBAT_ACTIONS = {ActionType.ATTACK, ActionType.SHOOT, ActionType.CAST_SPELL}
