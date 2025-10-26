from __future__ import annotations

import re
from abc import ABC
from typing import TYPE_CHECKING, Self

from agent.actions.base import Action, ActionType, BonusAction, StandardAction
from agent.character.stats import StatType
from agent.effects.status_effects.base import StatusEffect
from agent.equipment.weapons import RangedWeapon, Weapon, WeaponType
from agent.logs.events import Icon
from agent.models.constants import EventType
from agent.models.damage import Damage, DamageComponent, DamageType

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class AttackAction(Action, ABC):
    type: ActionType = ActionType.ATTACK
    damage_dice: str
    damage_type: DamageType
    weapon_type: WeaponType
    stat: StatType
    range: float
    status_effects: list[StatusEffect] = []

    def execute(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        self._fire_start_events(actor, target, ctx)
        self._resolve_attack(actor, target, ctx)

        # Apply damage if any
        if ctx.is_hit:
            self._apply_damage(actor, target, ctx)

        self._fire_end_events(actor, target, ctx)

    def _resolve_attack(self, actor: Character, target: Character, ctx: CombatContext) -> bool:
        roll = actor.attack_roll(attack_stat=self.stat, target=target)
        ctx.is_critical = ctx.is_critical or roll.raw == actor.attributes.crit_roll()

        ctx.hit_roll = roll
        ctx.is_hit = ctx.is_critical or roll.total >= target.armor_class

        if ctx.is_critical:
            # Critical guarantees a hit -> direct damage roll with critical
            actor.log_event("Rolls a NATURAL 20! Critical hit!", icon=Icon.ROLL)
        else:
            # Check attack roll result
            actor.log_event(f"Attack roll {roll.expression}: {roll.total} vs AC {target.armor_class}", icon=Icon.ROLL)
            if ctx.is_hit:
                actor.log_event("Attack roll passed → Hits target!", icon=Icon.ATTACK, show_ai=True)
            else:
                actor.log_event("Attack roll failed → Target missed...", icon=Icon.DEFENSE, show_ai=True)

        return ctx.is_hit

    def _apply_damage(self, actor: Character, target: Character, ctx: CombatContext) -> CombatContext:
        # Damage roll
        mod = self._attack_modifier(actor)
        expr = f"{self.damage_dice}+{mod}"
        droll = actor.damage_roll(expr=expr, is_critical=ctx.is_critical)
        ctx.damage_roll = droll
        ctx.damage = Damage(components=[DamageComponent(value=droll.total, type=self.damage_type)])
        actor.log_event(f"Damage roll: {droll.total}", icon=Icon.ROLL)

        # Apply actor status effects
        target.trigger_event(EventType.APPLY_DAMAGE, actor, target, ctx)

        # Apply target resistances and vulnerabilities
        ctx.damage = target.modify_incoming_damage(ctx.damage)

        # Apply target status effects
        target.trigger_event(EventType.RECEIVE_DAMAGE, actor, target, ctx)

        # Apply damage
        total_damage = ctx.damage.total
        target.apply_damage(damage=total_damage)
        actor.log_event(f"Damage dealt: {total_damage} ({ctx.damage})", icon=Icon.DAMAGE, show_ai=True)
        target.log_event(f"{target.name}: {target.attributes.hp}/{target.max_hp} HP")

        if not target.is_alive:
            target.log_event(f"{target.name} is defeated", icon=Icon.DEATH, show_ai=True)
            return ctx

        # Try to apply status effects
        for effect in self.status_effects:
            target.try_apply_effect(effect)

        return ctx

    def _attack_modifier(self, actor: Character) -> int:
        # Parse existing modifier from the dice expression (e.g. "1d8+2" → base="1d8", base_mod=2)
        match = re.match(r"^(\d+d\d+)([+-]\d+)?$", self.damage_dice.strip())
        if match:
            base_expr, base_mod_str = match.groups()
            base_mod = int(base_mod_str) if base_mod_str else 0
        else:
            base_mod = 0

        prof_bonus = actor.proficiency_bonus if self.weapon_type in actor.proficiencies else 0
        mod = actor.attributes.stat_modifier(self.stat)
        return base_mod + mod + prof_bonus

    def _fire_start_events(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        actor.trigger_event(EventType.COMBAT_START, actor, target, ctx)
        target.trigger_event(EventType.COMBAT_START, actor, target, ctx)

    def _fire_end_events(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        actor.trigger_event(EventType.COMBAT_END, actor, target, ctx)
        target.trigger_event(EventType.COMBAT_END, actor, target, ctx)

    def __str__(self) -> str:
        effects = ", ".join([str(eff) for eff in self.status_effects]) if self.status_effects else "None"
        return (
            f"{self.id}: {self.name} — {self.description} "
            f"(Type: {self.type.value}, Category: {self.category.value}, Targeting: {self.targeting.value}, "
            f"Stat: {self.stat.value}, Damage: {self.damage_dice} {self.damage_type.value}, "
            f"Range: {self.range} m, Hits: {self.hits}, Status Effects: {effects})"
        )


class MainHandAttackAction(StandardAction, AttackAction):
    id: str = "main_hand_attack"
    name: str = "Main Hand Attack"
    description: str = "Base attack with main hand weapon."
    type: ActionType = ActionType.ATTACK

    @classmethod
    def from_weapon(cls, weapon: Weapon) -> Self:
        return cls(
            description=f"Base Attack with main hand weapon {weapon.name}",
            weapon_type=weapon.weapon_type,
            targeting=weapon.targeting,
            damage_dice=weapon.damage_dice,
            damage_type=weapon.damage_type,
            stat=weapon.stat,
            range=weapon.range,
            status_effects=weapon.effects,
        )


class OffHandAttackAction(BonusAction, AttackAction):
    id: str = "off_hand_attack"
    name: str = "Off Hand Attack"
    description: str = ""
    type: ActionType = ActionType.OFF_HAND_ATTACK

    @classmethod
    def from_weapon(cls, weapon: Weapon) -> Self:
        return cls(
            description=f"Bonus Attack with off hand weapon {weapon.name}",
            weapon_type=weapon.weapon_type,
            targeting=weapon.targeting,
            damage_dice=weapon.damage_dice,
            damage_type=weapon.damage_type,
            stat=weapon.stat,
            range=weapon.range,
            status_effects=weapon.effects,
        )


class RangedAttackAction(StandardAction, AttackAction):
    id: str = "ranged_attack"
    name: str = "Ranged Attack"
    description: str = ""
    type: ActionType = ActionType.ATTACK

    @classmethod
    def from_weapon(cls, weapon: RangedWeapon) -> Self:
        return cls(
            description=f"Ranged Attack with {weapon.name}",
            weapon_type=weapon.weapon_type,
            targeting=weapon.targeting,
            damage_dice=weapon.damage_dice,
            damage_type=weapon.damage_type,
            stat=weapon.stat,
            range=weapon.range,
            status_effects=weapon.effects,
        )
