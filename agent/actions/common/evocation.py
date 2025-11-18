from __future__ import annotations

from typing import TYPE_CHECKING

from agent.actions.base import ActionType, StandardAction
from agent.character.abilities import AbilityType
from agent.character.resources import SpellLevel
from agent.effects.evocations.base import Evocation
from agent.logs.log_event import Icon
from agent.models.context import CombatContext
from agent.models.enums import TargetingType
from agent.models.position import Position

if TYPE_CHECKING:
    from agent.character.character import Character


class EvocationSpellAction(StandardAction):
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
        actor.add_evocation(self.evocation)
        actor.log_event(f"{actor.name} summons {self.name}")

        if self.self.evocation.on_cast_use is None:
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
