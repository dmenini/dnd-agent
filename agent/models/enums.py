from enum import Enum
from typing import Literal

PartyType = Literal["players", "enemies", "neutrals"]


class DamageType(str, Enum):
    BLUDGEONING = "bludgeoning"
    PIERCING = "piercing"
    SLASHING = "slashing"
    FIRE = "fire"
    COLD = "cold"
    LIGHTNING = "lightning"
    POISON = "poison"
    MAGIC = "magic"


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
