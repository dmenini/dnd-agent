"""Resource consumers for composable actions.

Resource consumers handle resource consumption:
- ActionEconomyConsumer: Consume action/bonus/reaction
- SpellSlotConsumer: Consume spell slots
- LimitedUsesConsumer: Consume limited-use resources
"""

from agent.actions.resources.action_economy import ActionEconomyConsumer
from agent.actions.resources.spell_slots import SpellSlotConsumer
from agent.actions.resources.limited_uses import LimitedUsesConsumer

__all__ = [
    "ActionEconomyConsumer",
    "SpellSlotConsumer",
    "LimitedUsesConsumer",
]
