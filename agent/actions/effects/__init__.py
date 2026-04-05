"""Effect applicators for composable actions.

Effect applicators apply the actual game effects:
- DamageEffect: Deal damage to target
- HealingEffect: Restore hit points
- ApplyConditionsEffect: Apply status effects
- RemoveConditionsEffect: Remove status effects
- SummonEvocationEffect: Summon an evocation at a position
"""

from agent.actions.effects.conditions import ApplyConditionsEffect, RemoveConditionsEffect
from agent.actions.effects.damage import DamageEffect
from agent.actions.effects.evocation import SummonEvocationEffect
from agent.actions.effects.healing import HealingEffect

__all__ = [
    "ApplyConditionsEffect",
    "DamageEffect",
    "HealingEffect",
    "RemoveConditionsEffect",
    "SummonEvocationEffect",
]
