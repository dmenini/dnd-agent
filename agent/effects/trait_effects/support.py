from __future__ import annotations

import math
from typing import TYPE_CHECKING

from agent.logs.events import EventType
from agent.models.context import CombatContext

if TYPE_CHECKING:
    from agent.character.resolvers.base import CharacterBase


def life_steal_effect(actor: CharacterBase, context: CombatContext, ratio: float) -> None:
    if context.damage:
        heal = math.ceil(context.damage.total * ratio)
        actor.heal(heal)
        actor.log_event(f"{actor.name} heals {heal} HP through life steal.", event_type=EventType.DEBUG)


def regeneration_effect(actor: CharacterBase, value: int) -> None:
    actor.heal(value)
    actor.log_event(f"{actor.name} heals {value} HP.", event_type=EventType.DEBUG)
