from __future__ import annotations

import math
from typing import TYPE_CHECKING

from agent.effects.base import register_effect
from agent.models.constants import TRAIT_LOG_LEVEL
from agent.services.combat_service import CombatService
from agent.services.roll_service import RollService

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


@register_effect()
def bonus_attack_roll_effect(_: Character, context: CombatContext, *, expr: str) -> None:
    if context.attack_roll:
        result = RollService.roll(expr)
        context.attack_roll.total += result.total


@register_effect()
def bonus_save_roll_effect(_: Character, context: CombatContext, *, expr: str) -> None:
    if context.save_roll:
        result = RollService.roll(expr)
        context.save_roll.total += result.total


@register_effect()
def life_steal_effect(actor: Character, context: CombatContext, ratio: float) -> None:
    if context.damage:
        heal = math.ceil(context.damage.total * ratio)
        CombatService.heal(actor, heal)  # type: ignore[arg-type]
        actor.log_event(f"{actor.name} heals {heal} HP through life steal.", log_type=TRAIT_LOG_LEVEL)


@register_effect()
def regeneration_effect(actor: Character, value: int) -> None:
    CombatService.heal(actor, value)  # type: ignore[arg-type]
    actor.log_event(f"{actor.name} heals {value} HP.", log_type=TRAIT_LOG_LEVEL)


@register_effect()
def healing_bonus_effect(_: Character, context: CombatContext, value: int) -> None:
    if context.heal_roll:
        spell_level = context.metadata.get("level", 1)
        context.heal_roll.total = spell_level + value
