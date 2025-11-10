from __future__ import annotations

import math
from typing import TYPE_CHECKING

from agent.models.constants import TRAIT_LOG_LEVEL

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.character.resolvers.base import CharacterBase
    from agent.models.context import CombatContext


def bonus_attack_roll_effect(actor: Character, context: CombatContext, *, expr: str) -> None:
    if context.attack_roll:
        result = actor.roll(expr=expr)
        context.attack_roll.total += result.total


def bonus_save_roll_effect(actor: Character, context: CombatContext, *, expr: str) -> None:
    if context.save_roll:
        result = actor.roll(expr=expr)
        context.save_roll.total += result.total


def life_steal_effect(actor: CharacterBase, context: CombatContext, ratio: float) -> None:
    if context.damage:
        heal = math.ceil(context.damage.total * ratio)
        actor.heal(heal)
        actor.log_event(f"{actor.name} heals {heal} HP through life steal.", log_type=TRAIT_LOG_LEVEL)


def regeneration_effect(actor: CharacterBase, value: int) -> None:
    actor.heal(value)
    actor.log_event(f"{actor.name} heals {value} HP.", log_type=TRAIT_LOG_LEVEL)
