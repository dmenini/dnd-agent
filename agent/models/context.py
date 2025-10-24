from anthropic import BaseModel

from agent.mechanics.dice_roller import DiceRoll
from agent.models.damage import Damage
from agent.models.map import GameMap


class CombatContext(BaseModel):
    map: GameMap | None = None
    hit_roll: DiceRoll | None = None
    damage_roll: DiceRoll | None = None
    damage: Damage | None = None
    is_critical: bool = False
    is_hit: bool | None = None
    metadata: dict = {}
