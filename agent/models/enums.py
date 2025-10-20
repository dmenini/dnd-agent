from enum import Enum
from typing import Literal

PartyType = Literal["players", "enemies", "neutrals"]


class Advantage(int, Enum):
    ADVANTAGE = 1
    NEUTRAL = 0
    DISADVANTAGE = -1


class TurnPhase(str, Enum):
    DECIDE = "decide"
    VERIFY = "verify"
    ROLL = "roll"
    EXECUTE = "execute"
    START = "start"
    END = "end"


class TargetingType(str, Enum):
    SINGLE = "single"
    AREA = "area"
    SELF = "self"
    MULTI = "multi"
