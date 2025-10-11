from pydantic import BaseModel


class Weapon(BaseModel):
    name: str
    damage_dice: str
    damage_type: str
    stat: str


class MeleeWeapon(Weapon):
    stat: str = "strength"


class RangeWeapon(Weapon):
    stat: str = "dexterity"


class Spell(Weapon):
    stat: str = "intelligence"
