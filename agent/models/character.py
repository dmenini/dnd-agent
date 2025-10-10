from pydantic import BaseModel


class Stats(BaseModel):
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10

    def modifier(self, stat: str) -> int:
        return (getattr(self, stat) - 10) // 2

    def advantage(self, stat_value: int) -> int:
        if stat_value >= 16:
            return 1
        if stat_value <= 8:
            return -1
        return 0


class Character(BaseModel):
    id: str
    name: str
    hp: int
    pos: tuple[int, int]
    is_player: bool = False
    stats: Stats = Stats()
