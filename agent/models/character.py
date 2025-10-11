from pydantic import BaseModel

from agent.models.enums import ActionType

DEFAULT_STAT = 10
ADVANTAGE_THRESHOLD = 16
DISADVANTAGE_THRESHOLD = 8


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


class Stats(BaseModel):
    strength: int = DEFAULT_STAT
    dexterity: int = DEFAULT_STAT
    constitution: int = DEFAULT_STAT
    intelligence: int = DEFAULT_STAT
    wisdom: int = DEFAULT_STAT
    charisma: int = DEFAULT_STAT

    def modifier(self, stat: str) -> int:
        val = self.__getattribute__(stat)
        return (val - DEFAULT_STAT) // 2

    def advantage(self, stat: str) -> bool | None:
        val = self.__getattribute__(stat)
        if val and val >= ADVANTAGE_THRESHOLD:
            return True
        if val and val <= DISADVANTAGE_THRESHOLD:
            return False
        return None

    def get_stat_from_action(self, action_type: ActionType) -> int:
        if action_type == ActionType.ATTACK:
            return self.strength
        if action_type == ActionType.SHOOT:
            return self.dexterity
        if action_type == ActionType.CAST_SPELL:
            return self.intelligence
        if action_type == ActionType.ROLEPLAY:
            return self.charisma
        return DEFAULT_STAT


class Character(BaseModel):
    id: str
    name: str
    pos: tuple[int, int]
    hp: int = 10
    ac: int = 5
    max_hp: int = 10
    crit_multiplier: int = 2
    is_player: bool = False
    stats: Stats
    melee_weapon: MeleeWeapon | None = None
    range_weapon: RangeWeapon | None = None
    spell: Spell | None = None
