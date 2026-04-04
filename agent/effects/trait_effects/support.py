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


@register_effect()
def guided_strike(actor: Character, target: Character, context: CombatContext) -> None:
    """Use Channel Divinity to add +10 to an attack roll.

    Automatically activated if:
    - Character has Channel Divinity uses available
    - The attack would miss without the bonus
    - The attack would hit with the bonus
    """
    if not context.attack_roll:
        return

    # Check if we have Channel Divinity uses available
    channel_divinity = actor.get_resource("channel_divinity")
    if not channel_divinity.has_uses():
        return

    # Use target AC
    target_ac = target.armor_class
    current_total = context.attack_roll.total

    # Only use if it would turn a miss into a hit
    would_miss = current_total < target_ac
    would_hit_with_bonus = (current_total + 10) >= target_ac

    if would_miss and would_hit_with_bonus:
        # Apply the bonus
        context.attack_roll.total += 10
        # Consume Channel Divinity
        channel_divinity.consume()
        actor.log_event(f"{actor.name} uses Guided Strike (+10 to attack roll)!", log_type=TRAIT_LOG_LEVEL)
