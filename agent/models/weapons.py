from pydantic import BaseModel


class Weapon(BaseModel):
    name: str
    damage_dice: str
    damage_type: str
    stat: str
    range: float


class MeleeWeapon(Weapon):
    stat: str = "strength"
    damage_type: str = "melee"


class FinesseWeapon(Weapon):
    stat: str = "dexterity"
    damage_type: str = "melee"


class RangeWeapon(Weapon):
    stat: str = "dexterity"
    damage_type: str = "range"


class Spell(Weapon):
    stat: str = "intelligence"
    damage_type: str = "magic"
