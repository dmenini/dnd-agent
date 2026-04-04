from collections.abc import Sequence

from anthropic import BaseModel
from pydantic import Field

from agent.character.character import Character
from agent.mechanics.dice_roller import DiceRoll
from agent.models.damage import Damage
from agent.models.map import GameMap


class CombatContext(BaseModel):
    enemies: Sequence[Character] = Field(default_factory=list)
    allies: Sequence[Character] = Field(default_factory=list)
    hits: dict[str, int] = Field(default_factory=dict)
    map: GameMap | None = None
    damage_roll: DiceRoll | None = None
    attack_roll: DiceRoll | None = None
    save_roll: DiceRoll | None = None
    heal_roll: DiceRoll | None = None
    damage: Damage | None = None
    is_critical: bool = False
    is_hit: bool | None = None
    metadata: dict = Field(default_factory=dict)
