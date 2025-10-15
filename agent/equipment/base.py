from pydantic import BaseModel

from agent.character.stats import StatType
from agent.effects.base import StatusEffect
from agent.models.enums import TargetingType


class Equipment(BaseModel):
    name: str
    targeting: TargetingType
    stat: StatType
    range: float
    description: str = ""
    status_effects: list[StatusEffect] = []
