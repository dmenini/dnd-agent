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


class ConditionType(str, Enum):
    STUNNED = "stunned"
    PARALYZED = "paralyzed"
    POISONED = "poisoned"
    PRONE = "prone"
    UNCONSCIOUS = "unconscious"
    DODGING = "dodging"


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
    AOE_SPELL = "aoe_spell"
    UTILITY = "utility"
    SPECIAL = "special"
    DASH = "dash"
    MOVE = "move"
    DODGE = "DODGE"


class WeaponType(str, Enum):
    # Simple Melee
    CLUB = "club"
    DAGGER = "dagger"
    GREATCLUB = "greatclub"
    HANDAXE = "handaxe"
    JAVELIN = "javelin"
    LIGHT_HAMMER = "light_hammer"
    MACE = "mace"
    QUARTERSTAFF = "quarterstaff"
    SICKLE = "sickle"
    SPEAR = "spear"

    # Simple Ranged
    CROSSBOW_LIGHT = "light_crossbow"
    DART = "dart"
    SHORTBOW = "shortbow"
    SLING = "sling"

    # Martial Melee
    BATTLEAXE = "battleaxe"
    FLAIL = "flail"
    GLAIVE = "glaive"
    GREATAXE = "greataxe"
    GREATSWORD = "greatsword"
    HALBERD = "halberd"
    LANCE = "lance"
    LONGSWORD = "longsword"
    MAUL = "maul"
    MORNINGSTAR = "morningstar"
    PIKE = "pike"
    RAPIR = "rapier"
    SCIMITAR = "scimitar"
    SHORTSWORD = "shortsword"
    TRIDENT = "trident"
    WARHAMMER = "warhammer"
    WHIP = "whip"

    # Martial Ranged
    BLOWGUN = "blowgun"
    CROSSBOW_HEAVY = "heavy_crossbow"
    LONGBOW = "longbow"
    NET = "net"

    # Other / Custom
    OTHER = "other"
    SPELL = "spell"


class SpellLevel(Enum):
    CANTRIP = 0
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
