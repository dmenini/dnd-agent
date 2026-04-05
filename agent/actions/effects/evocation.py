"""Evocation effect applicator."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from agent.actions.effects.base import EffectApplicator
from agent.effects.evocations.base import Evocation
from agent.logs.log_event import Icon
from agent.models.position import Position
from agent.services.evocation_service import EvocationService

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class SummonEvocationEffect(EffectApplicator):
    """Summon an evocation at a target position.

    Used for:
    - Spiritual Weapon (Cleric War Domain)
    - Spirit Guardians (Cleric)
    - Flaming Sphere (Wizard)
    - Other summoning spells that create controllable entities

    The evocation is summoned at the target position and can perform actions
    according to its features. If `on_cast_action_id` is specified, the evocation
    will immediately attempt to use that action against the nearest enemy.
    """

    type: Literal["summon_evocation"] = "summon_evocation"
    evocation: Evocation = Field(description="The evocation to summon")
    on_cast_action_id: str | None = Field(default=None, description="Feature ID to immediately use after summoning")

    def apply(self, actor: Character, target: Character | Position, ctx: CombatContext) -> None:
        """Summon the evocation at target position.

        Args:
            actor: Character casting the spell
            target: Position where evocation should be summoned (Character target uses their position)
            ctx: Combat context
        """
        # Determine position
        position = target if isinstance(target, Position) else target.pos

        # Set evocation position and summon
        self.evocation.position = position
        EvocationService.add_evocation(actor, self.evocation)
        actor.log_event(f"{actor.name} summons {self.evocation.name} at position {position}.")

        # Execute on-cast action if specified
        if self.on_cast_action_id is None:
            return

        # Find the matching feature
        feat = next(
            (feat for feat in self.evocation.features if feat.ref_id.value == self.on_cast_action_id),
            None,
        )
        if feat is None:
            actor.log_event(f"ERROR: Feature {self.on_cast_action_id} not found in evocation.", icon=Icon.WARNING)
            return

        action = feat.to_action()

        # Find the nearest enemy within range
        if ctx.map is None:
            raise ValueError

        alive_enemies = {enemy.id: enemy for enemy in ctx.enemies if enemy.is_alive}
        target_enemy = None
        for char_id in ctx.map.find_nearest(position, max_range=action.range):
            enemy = alive_enemies.get(char_id)
            if enemy is not None:
                target_enemy = enemy
                break

        if target_enemy is None:
            actor.log_event(f"No enemy in range for {action.name}")
            return

        # Perform the action
        actor.log_event(f"{self.evocation.name} performs {action.name} on {target_enemy.name}")
        action.execute(actor, target_enemy, ctx)

        # Block further actions on the same turn
        self.evocation.action_economy.can_act = False
        self.evocation.action_economy.movement_available = False
