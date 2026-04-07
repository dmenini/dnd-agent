"""Distributed effect applicators for multi-target resource division."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from agent.actions.effects.base import EffectApplicator
from agent.actions.expressions import ExpressionEvaluator
from agent.logs.log_event import LogLevel
from agent.services.combat_service import CombatService

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class DistributedHealingEffect(EffectApplicator):
    """Divide a healing pool across multiple targets.

    Used for:
    - Preserve Life (Cleric): divide healing pool across allies
    - Mass healing effects with limited total
    - Resource distribution abilities
    """

    type: Literal["distributed_healing"] = Field(default="distributed_healing", description="Effect type identifier")
    total_amount: str | int = Field(
        default="{level} * 5", description="Expression for total healing pool (e.g., '{level} * 5', '30')"
    )
    max_per_target: str | int | None = Field(
        default="{target.max_hp} / 2",
        description="Per-target healing cap, None for no limit. Supports expressions.",
        examples=["{target.max_hp} / 2", 10, None],
    )
    min_per_target: int = Field(
        default=0, description="Minimum healing per target (skip target if can't meet threshold)"
    )
    distribution_strategy: Literal["equal", "most_wounded_first", "percentage"] = Field(
        default="equal", description="How to distribute healing across targets"
    )

    def apply(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        """Apply distributed healing to target.

        Note: This is called once per target. The total pool is divided based on
        the number of targets specified in ctx.hits.
        """
        # Evaluate total healing pool
        total_pool = int(ExpressionEvaluator.eval(self.total_amount, actor, None, ctx))

        # Count number of targets
        num_targets = sum(1 for hits in ctx.hits.values() if hits > 0)
        if num_targets == 0:
            return

        # Calculate healing for this target based on strategy
        if self.distribution_strategy == "equal":
            heal_amount = total_pool // num_targets
        elif self.distribution_strategy == "most_wounded_first":
            # This is simplified - in a full implementation, you'd sort all targets
            # and distribute more to heavily wounded targets
            heal_amount = total_pool // num_targets
        elif self.distribution_strategy == "percentage":
            # Heal based on how much HP the target is missing
            missing_hp = target.max_hp - target.attributes.hp
            heal_amount = int(total_pool * (missing_hp / target.max_hp)) if target.max_hp > 0 else 0
        else:
            heal_amount = total_pool // num_targets

        # Apply per-target cap if specified
        if self.max_per_target is not None:
            max_allowed = int(ExpressionEvaluator.eval(self.max_per_target, actor, target, ctx))
            heal_amount = min(heal_amount, max_allowed)

        # Apply minimum threshold
        if heal_amount < self.min_per_target:
            actor.log_event(
                f"{target.name} does not receive healing (below minimum threshold)",
                log_type=LogLevel.DETAIL,
            )
            return

        # Can't heal beyond max HP
        heal_amount = min(heal_amount, target.max_hp - target.attributes.hp)

        # Apply healing
        if heal_amount > 0:
            CombatService.heal(target, heal_amount)
            actor.log_event(
                f"{actor.name} channels divine light to heal {target.name} "
                f"for {heal_amount} HP ({target.attributes.hp}/{target.max_hp})",
                log_type=LogLevel.DETAIL,
            )
