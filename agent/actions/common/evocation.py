from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import PrivateAttr

from agent.actions.base import ActionType, BonusAction
from agent.actions.common.move import MovementAction
from agent.character.abilities import AbilityType
from agent.character.resources import SpellLevel
from agent.effects.evocations.base import Evocation
from agent.logs.log_event import Icon
from agent.models.enums import FeatureId, TargetingType
from agent.models.position import Position

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class RepositionEvocationAction(MovementAction):
    id: str = FeatureId.REPOSITION_EVOCATION.value
    name: str = "Reposition Evocation"
    description: str = "Move evocation to a new position within the range, or turn towards a new direction."
    evocation_name: str

    _distance: float = PrivateAttr(default=0)

    def execute(self, actor: Character, target: Position, ctx: CombatContext) -> None:
        if not ctx.map:
            raise ValueError

        dist = ctx.map.distance(start=actor.pos, end=target)
        if dist is None or dist > self.range:
            msg = "Target position cannot be reached"
            raise ValueError(msg)

        self._distance = dist
        evo = next(evo for evo in actor.evocations if evo.name == self.evocation_name)
        evo.position = target

    def finalize(self, actor: Character) -> None:
        """Consume movement."""
        movement_cost = self._distance
        evo = next(evo for evo in actor.evocations if evo.name == self.evocation_name)
        evo.action_economy.use_movement(distance=movement_cost)
        self._distance = 0


class EvocationSpellAction(BonusAction):
    id: str
    name: str
    description: str = ""
    type: ActionType = ActionType.CAST_SPELL
    level: SpellLevel
    targeting: TargetingType
    ability: AbilityType
    range: float
    evocation: Evocation

    def execute(self, actor: Character, target: Position, ctx: CombatContext) -> None:
        if actor.los_distance(target) > self.range:
            msg = "Cannot summon evocation to a position farther than maximum spell range"
            raise ValueError(msg)

        self.evocation.position = target
        actor.add_evocation(self.evocation)
        actor.log_event(f"{actor.name} summons {self.name} at position {target}.")

        if self.evocation.on_cast_use is None:
            return

        # Find the matching feature → action
        feat = next(
            (feat for feat in self.evocation.features if feat.ref_id == self.evocation.on_cast_use),
            None,
        )
        if feat is None:
            actor.log_event(f"ERROR: Feature {self.evocation.on_cast_use} not found in evocation.", icon=Icon.WARNING)
            return

        action = feat.to_action()

        # Find the nearest enemy within range
        alive_enemies = {enemy.id: enemy for enemy in ctx.enemies if enemy.is_alive}

        if ctx.map is None:
            raise ValueError

        target_enemy = None
        for char_id in ctx.map.find_nearest(target, max_range=action.range):
            enemy = alive_enemies.get(char_id)
            if enemy is not None:
                target_enemy = enemy
                break

        if target_enemy is None:
            actor.log_event(f"No enemy in range for {action.name}")
            return

        # Perform the action
        actor.log_event(f"{self.name} performs {action.name} on {target_enemy.name}")
        action.execute(actor, target_enemy, ctx)

        # Block further actions on the same turn
        self.evocation.action_economy.can_act = False
        self.evocation.action_economy.movement_available = False

    def finalize(self, actor: Character) -> None:
        """Consume action point and spell slot."""
        super().finalize(actor)
        actor.spell_slots.consume(self.level)

    def __str__(self) -> str:
        level = f" Level {self.level.value}" if self.level != SpellLevel.CANTRIP else ""
        return (
            f"- {self.id}: {self.name}{level} — {self.description} "
            f"(Type: {self.type.value}, Category: {self.category.value}, Targeting: {self.targeting.value}, "
            f"Range: {self.range} m, Hits: {self.hits})"
        )
