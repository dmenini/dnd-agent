"""Saving throw resolution strategy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from agent.actions.strategies.base import ResolutionStrategy
from agent.character.abilities import AbilityType
from agent.logs.log_event import Icon
from agent.models.enums import EventType
from agent.services.roll_service import RollService
from agent.services.trait_service import TraitService

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class SavingThrowStrategy(ResolutionStrategy):
    """Target rolls save vs caster's DC.

    This is the standard resolution for spells like Fireball, Poison Spray, etc.

    Flow:
    1. Target rolls d20 + ability modifier + proficiency
    2. Compare vs caster's spell save DC (or ability DC)
    3. Save succeeds if roll >= DC
    4. Action succeeds if save FAILS (inverted logic)

    Note: Some effects apply on failed save (full damage), others apply reduced
    effects on success (half damage). That's handled by the effect, not here.
    """

    ability: AbilityType  # Which save: DEX, CON, WIS, etc.
    use_spell_dc: bool = True  # Use spell DC or ability DC

    def resolve(self, actor: Character, target: Character, ctx: CombatContext) -> bool:
        """Resolve saving throw vs caster DC."""
        # Determine DC
        if self.use_spell_dc:
            dc = actor.spell_save_dc
        else:
            dc = actor.attributes.ability_dc(self.ability)

        # Target rolls save
        roll = RollService.save_roll(target, ability=self.ability, is_spell=self.use_spell_dc)

        # Store in context
        ctx.save_roll = roll

        # Trigger trait events (allows traits to modify save)
        TraitService.trigger_event(actor, EventType.SAVE_THROW, actor, target, ctx)

        # Determine result (inverted: failed save = hit)
        ctx.is_hit = ctx.save_roll.total < dc

        # Logging
        actor.log_event(
            f"{self.ability.name} save throw {roll.expression}: {roll.total} vs DC {dc}",
            icon=Icon.ROLL
        )

        if ctx.is_hit:
            actor.log_event("Save roll failed → Hits target!", icon=Icon.ATTACK, show_ai=True)
        else:
            actor.log_event(f"Save roll passed → Target resists!", icon=Icon.DEFENSE, show_ai=True)

        return ctx.is_hit
