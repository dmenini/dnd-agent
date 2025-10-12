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


class TargetingType(str, Enum):
    SINGLE = "single"
    MULTI = "multi"
    AREA = "area"


class ActionCategory(str, Enum):
    STANDARD = "standard"
    BONUS = "bonus"
    REACTION = "reaction"
    MOVEMENT = "movement"


class ActionType(str, Enum):
    MELEE_ATTACK = "melee_attack"
    RANGED_ATTACK = "ranged_attack"
    SPELL = "spell"
    AOE_SPELL = "aoe_spell"
    UTILITY = "utility"
    SPECIAL = "special"
