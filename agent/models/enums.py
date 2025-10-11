from enum import Enum


class TurnPhase(str, Enum):
    DECIDE = "decide"
    VERIFY = "verify"
    ROLL = "roll"
    EXECUTE = "execute"


class ActionType(str, Enum):
    ATTACK = "attack"
    SHOOT = "shoot"
    MOVE = "move"
    CAST_SPELL = "cast_spell"
    ROLEPLAY = "roleplay"
    WAIT = "wait"
