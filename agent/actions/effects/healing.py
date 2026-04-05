"""Healing effect applicator."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal

from agent.actions.effects.base import EffectApplicator
from agent.character.abilities import AbilityType
from agent.logs.log_event import Icon, LogLevel
from agent.models.enums import EventType
from agent.services.combat_service import CombatService
from agent.services.roll_service import RollService
from agent.services.trait_service import TraitService

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class HealingEffect(EffectApplicator):
    """Restore hit points.

    Flow:
    1. Roll healing dice (with template variable support)
    2. Trigger trait events (for healing bonuses like Disciple of Life)
    3. Cap at target's max HP
    4. Apply healing
    5. Log results

    Template variables supported in heal_dice:
    - {level} → actor.level
    - {proficiency_bonus} → actor.attributes.proficiency_bonus
    """

    type: Literal["healing"] = "healing"
    heal_dice: str
    ability: AbilityType | None = None

    def _parse_expression(self, expr: str, actor: Character) -> str:
        """Parse template variables in the expression.

        Supported variables:
        - {level} → actor.level
        - {proficiency_bonus} → actor.attributes.proficiency_bonus
        """
        replacements = {
            "level": str(actor.level),
            "proficiency_bonus": str(actor.attributes.proficiency_bonus),
        }

        for var, value in replacements.items():
            expr = re.sub(rf"\{{{var}\}}", value, expr)

        return expr

    def apply(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        """Apply healing to target."""
        # Parse template variables
        expr = self._parse_expression(self.heal_dice, actor)

        # Roll healing (use spell-based healing if ability is specified, otherwise generic roll)
        if self.ability is not None or actor.attributes.spellcasting_ability is not None:
            ctx.heal_roll = RollService.heal_roll(actor, expr=expr)
        else:
            # For non-spellcasting healing (like Second Wind), just roll the dice
            ctx.heal_roll = RollService.roll(expr, actor)

        # Trigger trait events (allows bonuses like Disciple of Life)
        TraitService.trigger_event(actor, EventType.HEAL, actor, target, ctx)

        # Cap at max HP
        heal_amount = min(ctx.heal_roll.total, target.max_hp - target.attributes.hp)

        if heal_amount > 0:
            CombatService.heal(target, heal_amount)
            target.log_event(
                f"{actor.name} heals {target.name} for {heal_amount} HP ({target.attributes.hp}/{target.max_hp}).",
                log_type=LogLevel.DETAIL,
                icon=Icon.EFFECT_APPLIED,
            )
        else:
            actor.log_event(f"{target.name} is already at full health", icon=Icon.WARNING)
