"""Resource consumers for composable actions.

Resource consumers handle resource consumption:
- ActionEconomyConsumer: Consume action/bonus/reaction
- SpellSlotConsumer: Consume spell slots
- LimitedUsesConsumer: Consume limited-use resources
"""

from agent.actions.resources.action_economy import ActionEconomyConsumer
from agent.actions.resources.limited_uses import LimitedUsesConsumer
from agent.actions.resources.spell_slots import SpellSlotConsumer

__all__ = [
    "ActionEconomyConsumer",
    "LimitedUsesConsumer",
    "SpellSlotConsumer",
]
