"""Attack roll resolution strategy."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

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

    Examples:
        Melee weapon attack: {"type": "attack_roll", "ability": "strength", "weapon_type": "martial_melee"}
        Ranged weapon attack: {"type": "attack_roll", "ability": "dexterity", "weapon_type": "simple_range"}
        Spell attack: {"type": "attack_roll", "ability": "intelligence", "weapon_type": "magic"}
    """

    type: Literal["attack_roll"] = "attack_roll"
    ability: AbilityType = Field(
        description=(
            "Ability score used for attack roll: strength, dexterity, intelligence, wisdom, charisma, or constitution"
        ),
        examples=["strength", "dexterity", "intelligence"],
    )
    weapon_type: WeaponType = Field(
        description="Weapon proficiency type: simple_melee, martial_melee, simple_range, martial_range, or magic",
        examples=["martial_melee", "simple_range", "magic"],
    )

    def resolve(self, actor: Character, target: Character, ctx: CombatContext) -> bool:
        """Resolve attack roll vs target AC."""
        # Roll attack
        roll = RollService.attack_roll(actor, ability=self.ability, weapon=self.weapon_type, target=target)

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
            actor.log_event(f"Attack roll {roll.expression}: {roll.total} vs AC {target.armor_class}", icon=Icon.ROLL)

            if ctx.is_hit:
                actor.log_event("Attack roll passed → Hits target!", icon=Icon.ATTACK, show_ai=True)
            else:
                actor.log_event("Attack roll failed → Target missed...", icon=Icon.DEFENSE, show_ai=True)

        return ctx.is_hit
