"""Effect applicators for composable actions.

Effect applicators apply the actual game effects:
- DamageEffect: Deal damage to target
- HealingEffect: Restore hit points
- ApplyConditionsEffect: Apply status effects
- RemoveConditionsEffect: Remove status effects
- SummonEvocationEffect: Summon an evocation at a position
- RecoverSpellSlotsEffect: Recover expended spell slots
- RestoreResourceEffect: Restore limited resources
- ApplyDynamicStatusEffect: Apply status with dynamic traits
- DistributedHealingEffect: Divide healing pool across targets
"""

from agent.actions.effects.conditions import ApplyConditionsEffect, RemoveConditionsEffect
from agent.actions.effects.damage import DamageEffect
from agent.actions.effects.distributed import DistributedHealingEffect
from agent.actions.effects.dynamic_status import ApplyDynamicStatusEffect
from agent.actions.effects.evocation import SummonEvocationEffect
from agent.actions.effects.healing import HealingEffect
from agent.actions.effects.resources import RecoverSpellSlotsEffect, RestoreResourceEffect

__all__ = [
    "ApplyConditionsEffect",
    "ApplyDynamicStatusEffect",
    "DamageEffect",
    "DistributedHealingEffect",
    "HealingEffect",
    "RecoverSpellSlotsEffect",
    "RemoveConditionsEffect",
    "RestoreResourceEffect",
    "SummonEvocationEffect",
]
