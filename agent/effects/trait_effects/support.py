from __future__ import annotations

import math
from typing import TYPE_CHECKING

from agent.character.modifier import Modifier
from agent.logs.events import Icon
from agent.models.constants import TRAIT_LOG_LEVEL

if TYPE_CHECKING:
    from agent.character.resolvers.base import CharacterBase
    from agent.models.context import CombatContext


def apply_modifier(target: CharacterBase, mod: Modifier, *, condition: bool = True) -> None:
    if condition:
        target.attributes.add_modifier(modifier=mod)
        target.log_event(
            f"Added modifier {mod.attribute}={mod.value} to {target.name}",
            icon=Icon.EFFECT_APPLIED,
            log_type=TRAIT_LOG_LEVEL,
        )


def life_steal_effect(actor: CharacterBase, context: CombatContext, ratio: float) -> None:
    if context.damage:
        heal = math.ceil(context.damage.total * ratio)
        actor.heal(heal)
        actor.log_event(f"{actor.name} heals {heal} HP through life steal.", log_type=TRAIT_LOG_LEVEL)


def regeneration_effect(actor: CharacterBase, value: int) -> None:
    actor.heal(value)
    actor.log_event(f"{actor.name} heals {value} HP.", log_type=TRAIT_LOG_LEVEL)
