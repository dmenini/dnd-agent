from anthropic import BaseModel
from pydantic import ConfigDict

from agent.mechanics.dice_roller import DiceRoll, DiceRoller
from agent.models.damage import Damage


class CombatContext(BaseModel):
    hit_roll: DiceRoll | None = None
    damage_roll: DiceRoll | None = None
    damage: Damage | None = None
    is_critical: bool = False
    is_hit: bool | None = None
    metadata: dict = {}
    dice: DiceRoller

    model_config = ConfigDict(arbitrary_types_allowed=True)
