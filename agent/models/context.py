from collections.abc import Sequence

from anthropic import BaseModel

from agent.character.resolvers.base import CharacterBase
from agent.mechanics.dice_roller import DiceRoll
from agent.models.damage import Damage
from agent.models.map import GameMap


class CombatContext(BaseModel):
    enemies: Sequence[CharacterBase] = []
    map: GameMap | None = None
    damage_roll: DiceRoll | None = None
    attack_roll: DiceRoll | None = None
    save_roll: DiceRoll | None = None
    damage: Damage | None = None
    is_critical: bool = False
    is_hit: bool | None = None
    metadata: dict = {}
