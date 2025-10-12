from enum import Enum
from typing import Literal

PartyType = Literal["players", "enemies", "neutrals"]


class StatType(str, Enum):
    STR = "strength"
    DEX = "dexterity"
    CON = "constitution"
    INT = "intelligence"
    WIS = "wisdom"
    CHA = "charisma"


class DamageType(str, Enum):
    BLUDGEONING = "bludgeoning"
    PIERCING = "piercing"
    SLASHING = "slashing"
    FIRE = "fire"
    COLD = "cold"
    LIGHTNING = "lightning"
    POISON = "poison"
    MAGIC = "magic"


class Condition(str, Enum):
    STUNNED = "stunned"
    PARALYZED = "paralyzed"
    POISONED = "poisoned"
    PRONE = "prone"
    UNCONSCIOUS = "unconscious"


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
