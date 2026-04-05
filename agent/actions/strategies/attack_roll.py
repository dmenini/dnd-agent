"""Attack roll resolution strategy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from agent.actions.strategies.base import ResolutionStrategy
from agent.character.abilities import AbilityType
from agent.equipment.weapons import WeaponType
from agent.logs.log_event import Icon
from agent.models.enums import EventType
from agent.services.roll_service import RollService
from agent.services.trait_service import TraitService

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class AttackRollStrategy(ResolutionStrategy):
    """Roll d20 + modifiers vs target AC.

    This is the standard resolution for weapon attacks and some spells
    (e.g., Eldritch Blast, Ray of Frost).

    Flow:
    1. Roll d20 + ability modifier + proficiency + other bonuses
    2. Check for critical hit (natural 20 or meets crit threshold)
    3. Compare total vs target AC
    4. Log results
    """

    ability: AbilityType
    weapon_type: WeaponType

    def resolve(self, actor: Character, target: Character, ctx: CombatContext) -> bool:
        """Resolve attack roll vs target AC."""
        # Roll attack
        roll = RollService.attack_roll(
            actor,
            ability=self.ability,
            weapon=self.weapon_type,
            target=target
        )

        # Check for critical
        ctx.is_critical = ctx.is_critical or roll.raw >= actor.attributes.crit_roll()

        # Store roll in context
        ctx.attack_roll = roll

        # Trigger trait events (allows traits to modify roll/crit)
        TraitService.trigger_event(actor, EventType.ATTACK_ROLL, actor, target, ctx)

        # Determine hit
        ctx.is_hit = ctx.is_critical or ctx.attack_roll.total >= target.armor_class

        # Logging
        if ctx.is_critical:
            actor.log_event(f"Rolls a NATURAL {roll.raw}! Critical hit!", icon=Icon.ROLL)
        else:
            actor.log_event(
                f"Attack roll {roll.expression}: {roll.total} vs AC {target.armor_class}",
                icon=Icon.ROLL
            )

            if ctx.is_hit:
                actor.log_event("Attack roll passed → Hits target!", icon=Icon.ATTACK, show_ai=True)
            else:
                actor.log_event("Attack roll failed → Target missed...", icon=Icon.DEFENSE, show_ai=True)

        return ctx.is_hit
