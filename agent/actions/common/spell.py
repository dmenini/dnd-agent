from __future__ import annotations

from typing import TYPE_CHECKING

from agent.actions.base import ActionType, StandardAction
from agent.actions.common.attack import AttackAction
from agent.character.resources import SpellLevel
from agent.character.stats import StatType
from agent.effects.status_effects.base import StatusEffect
from agent.equipment.weapons import WeaponType
from agent.logs.events import Icon
from agent.models.enums import (
    TargetingType,
)

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class AttackSpellAction(StandardAction, AttackAction):
    id: str
    name: str
    description: str = ""
    action_type: ActionType = ActionType.CAST_SPELL
    weapon_type: WeaponType = WeaponType.MAGIC
    level: SpellLevel
    requires_save: bool = True
    hits: int = 1

    def execute(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        self._fire_start_events(actor, target, ctx)
        is_hit = not self.requires_save or self._resolve_saving_throw(actor, target, ctx)

        # Apply damage if any
        if is_hit:
            self._apply_damage(actor, target, ctx)

        self._fire_end_events(actor, target, ctx)

    def _resolve_saving_throw(self, actor: Character, target: Character, ctx: CombatContext) -> bool:
        dc = actor.spell_save_dc
        save_roll = target.save_roll(save_stat=actor.attributes.spellcasting_stat, is_spell=True)

        ctx.hit_roll = save_roll
        ctx.is_hit = save_roll.total < dc

        actor.log_event(f"{self.stat.name} save: {save_roll.total} vs DC {dc}", icon=Icon.ROLL)

        if ctx.is_hit:
            actor.log_event(f"Save roll passed → Target resists {self.name}!", icon=Icon.DEFENSE, show_ai=True)
        else:
            actor.log_event("Save roll failed → Hits target!", icon=Icon.ATTACK, show_ai=True)

        return ctx.is_hit

    def finalize(self, actor: Character) -> None:
        """Consume action point and spell slot."""
        super().finalize(actor)
        actor.spell_slots.consume(self.level)


class SupportSpellAction(StandardAction):
    id: str
    name: str
    description: str = ""
    action_type: ActionType = ActionType.CAST_SPELL
    level: SpellLevel
    targeting: TargetingType
    stat: StatType
    range: float
    status_effects: list[StatusEffect] = []

    def execute(self, actor: Character, target: Character | None, ctx: CombatContext) -> None:  # noqa: ARG002
        if self.targeting == TargetingType.SELF:
            self._execute_on_target(target=actor)
        else:
            if target is None:
                raise ValueError
            self._execute_on_target(target=target)

    def _execute_on_target(self, target: Character) -> None:
        for effect in self.status_effects:
            target.try_apply_effect(effect)

    def finalize(self, actor: Character) -> None:
        """Consume action point and spell slot."""
        super().finalize(actor)
        actor.spell_slots.consume(self.level)
