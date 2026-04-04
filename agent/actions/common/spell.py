from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from agent.actions.base import ActionType, StandardAction
from agent.actions.common.attack import AttackAction
from agent.character.abilities import AbilityType
from agent.character.resources import SpellLevel
from agent.effects.status_effects.base import StatusEffect, StatusType
from agent.equipment.weapons import WeaponType
from agent.logs.log_event import Icon, LogLevel
from agent.models.enums import (
    EventType,
    TargetingType,
)

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class AttackSpellAction(StandardAction, AttackAction):
    id: str
    name: str
    description: str = ""
    type: ActionType = ActionType.CAST_SPELL
    weapon_type: WeaponType = WeaponType.MAGIC
    level: SpellLevel
    requires_save: bool = True
    hits: int = 1

    def execute(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        self._fire_start_events(actor, target, ctx)
        # TODO: Some spells require an attack roll, using the spellcaster ability as modifier
        is_hit = not self.requires_save or self._resolve_saving_throw(actor, target, ctx)

        # Apply damage if any
        if is_hit:
            self._apply_damage(actor, target, ctx)

        self._fire_end_events(actor, target, ctx)

    def _resolve_saving_throw(self, actor: Character, target: Character, ctx: CombatContext) -> bool:
        dc = actor.spell_save_dc
        roll = target.save_roll(ability=self.ability, is_spell=True)
        ctx.save_roll = roll
        actor.trigger_event(EventType.SAVE_THROW, actor, target, ctx)

        ctx.is_hit = ctx.save_roll.total < dc

        actor.log_event(f"{self.ability.name} save throw {roll.expression}: {roll.total} vs DC {dc}", icon=Icon.ROLL)

        if ctx.is_hit:
            actor.log_event(f"Save roll passed → Target resists {self.name}!", icon=Icon.DEFENSE, show_ai=True)
        else:
            actor.log_event("Save roll failed → Hits target!", icon=Icon.ATTACK, show_ai=True)

        return ctx.is_hit

    def finalize(self, actor: Character) -> None:
        """Consume action point and spell slot."""
        super().finalize(actor)
        actor.spell_slots.consume(self.level)

    def __str__(self) -> str:
        effects = ", ".join([str(eff) for eff in self.status_effects]) if self.status_effects else "None"
        level = f" Level {self.level.value}" if self.level != SpellLevel.CANTRIP else ""
        return (
            f"- {self.id}: {self.name}{level} — {self.description} "
            f"(Type: {self.type.value}, Category: {self.category.value}, Targeting: {self.targeting.value}, "
            f"Damage: {self.damage_dice} {self.damage_type.value}, "
            f"Range: {self.range} m, Hits: {self.hits}, Status Effects: {effects})"
        )


class SupportSpellAction(StandardAction):
    id: str
    name: str
    description: str = ""
    type: ActionType = ActionType.CAST_SPELL
    level: SpellLevel
    targeting: TargetingType
    ability: AbilityType
    range: float
    apply_conditions: list[StatusEffect] = Field(default_factory=list)
    remove_conditions: list[StatusType] = Field(default_factory=list)

    def execute(self, actor: Character, target: Character | None, ctx: CombatContext) -> None:  # noqa: ARG002
        if self.targeting == TargetingType.SELF:
            self._execute_on_target(target=actor)
        else:
            if target is None:
                raise ValueError
            self._execute_on_target(target=target)

    def _execute_on_target(self, target: Character) -> None:
        for to_apply in self.apply_conditions:
            target.try_apply_condition(to_apply)

        # Remove conditions
        for to_remove in self.remove_conditions:
            if target.has_condition(to_remove):
                target.remove_condition(to_remove)
                break

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


class HealingSpellAction(StandardAction):
    id: str
    name: str
    description: str = ""
    type: ActionType = ActionType.CAST_SPELL
    level: SpellLevel
    targeting: TargetingType
    ability: AbilityType
    range: float
    heal_dice: str

    def execute(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        ctx.heal_roll = actor.heal_roll(expr=self.heal_dice)
        actor.trigger_event(EventType.HEAL, actor, ctx)

        heal_amount = min(ctx.heal_roll.total, target.max_hp - target.attributes.hp)
        if heal_amount:
            target.heal(heal_amount)
            target.log_event(
                f"{actor.name} heals {target.name} for {heal_amount} HP ({target.attributes.hp}/{target.max_hp}).",
                log_type=LogLevel.DETAIL,
            )

    def finalize(self, actor: Character) -> None:
        """Consume action point and spell slot."""
        super().finalize(actor)
        actor.spell_slots.consume(self.level)

    def __str__(self) -> str:
        level = f" Level {self.level.value}" if self.level != SpellLevel.CANTRIP else ""
        return (
            f"- {self.id}: {self.name}{level} — {self.description} "
            f"(Type: {self.type.value}, Category: {self.category.value}, Targeting: {self.targeting.value}, "
            f"Heal dice: {self.heal_dice}, Range: {self.range} m)"
        )
