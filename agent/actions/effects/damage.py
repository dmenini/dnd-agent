"""Damage effect applicator."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal

from pydantic import Field

from agent.actions.effects.base import EffectApplicator
from agent.character.abilities import AbilityType
from agent.logs.log_event import Icon
from agent.models.damage import Damage, DamageComponent, DamageType
from agent.models.enums import EventType
from agent.services.combat_service import CombatService
from agent.services.roll_service import RollService
from agent.services.trait_service import TraitService

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class DamageEffect(EffectApplicator):
    """Deal damage to target.

    Flow:
    1. Roll damage dice (with template variable support and ability modifier if specified)
    2. Double dice on critical hit
    3. Apply resistances/vulnerabilities
    4. Trigger trait events (for damage bonuses, etc.)
    5. Apply damage to target HP
    6. Log results

    Template variables supported in damage_dice:
    - {level} → actor.level
    - {proficiency_bonus} → actor.attributes.proficiency_bonus

    Examples:
        Weapon attack:
            {"type": "damage", "damage_dice": "1d8+5", "damage_type": "slashing", "ability": "strength"}
        Fireball (half on save):
            {"type": "damage", "damage_dice": "8d6", "damage_type": "fire", "half_on_save": true}
        Scaled cantrip:
            {"type": "damage", "damage_dice": "{level}d10", "damage_type": "fire"}
    """

    type: Literal["damage"] = "damage"
    damage_dice: str = Field(
        description="Damage expression (e.g., '2d6', '3d8+5', '8d6'). Supports templates: {level}, {proficiency_bonus}",
        examples=["1d8+5", "8d6", "3d10", "{level}d10"],
    )
    damage_type: DamageType = Field(
        description="Type of damage",
    )
    ability: AbilityType | None = Field(
        default=None,
        description=(
            "Ability modifier to add to damage (e.g., strength for melee). None defaults to the class primary ability."
        ),
    )
    half_on_save: bool = Field(
        default=False,
        description="If true, deals half damage on successful save (common for AOE spells)",
    )

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

        for value in replacements.values():
            expr = re.sub(r"\{var}", value, expr)

        return expr

    def apply(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        """Apply damage to target."""
        # Parse template variables
        damage_expr = self._parse_expression(self.damage_dice, actor)

        # Roll damage
        is_critical = getattr(ctx, "is_critical", False)
        ctx.damage_roll = RollService.damage_roll(
            actor,
            damage_dice=damage_expr,
            ability=self.ability or actor.attributes.primary_ability,
            is_critical=is_critical,
        )

        # Half damage if save succeeded and half_on_save is True
        damage_value = ctx.damage_roll.total
        if self.half_on_save and not ctx.is_hit:
            damage_value = damage_value // 2
            actor.log_event(f"Target saved! Damage halved: {damage_value}", icon=Icon.DEFENSE)

        # Create damage object
        ctx.damage = Damage(components=[DamageComponent(value=damage_value, type=self.damage_type)])

        actor.log_event(f"Damage roll: {ctx.damage_roll.total}", icon=Icon.ROLL)

        # Apply target resistances and vulnerabilities
        ctx.damage = CombatService.modify_incoming_damage(target, ctx.damage)

        # Trigger trait events (for damage bonuses, etc.)
        TraitService.trigger_event(actor, EventType.APPLY_DAMAGE, actor, target, ctx)
        TraitService.trigger_event(target, EventType.RECEIVE_DAMAGE, actor, target, ctx)

        # Apply damage to HP
        total_damage = ctx.damage.total
        CombatService.apply_damage(target, total_damage)

        # Logging
        actor.log_event(f"Damage dealt: {total_damage} ({ctx.damage})", icon=Icon.DAMAGE, show_ai=True)
        target.log_event(f"{target.name}: {target.attributes.hp}/{target.max_hp} HP")

        if not target.is_alive:
            target.log_event(f"{target.name} is defeated", icon=Icon.DEATH, show_ai=True)
