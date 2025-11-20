from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Self

from agent.actions.base import Action, ActionType, BonusAction, StandardAction
from agent.character.abilities import Abilities, AbilityType
from agent.effects.status_effects.base import StatusEffect
from agent.effects.traits import TraitBuilder
from agent.equipment.weapons import MeleeWeapon, RangedWeapon, WeaponHandling, WeaponType
from agent.logs.log_event import Icon
from agent.models.constants import MELEE_RANGE
from agent.models.damage import Damage, DamageComponent, DamageType
from agent.models.enums import EventType, FeatureId

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


class AttackAction(Action, ABC):
    type: ActionType = ActionType.ATTACK
    damage_dice: str
    damage_type: DamageType
    weapon_type: WeaponType
    ability: AbilityType
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
        roll = actor.attack_roll(ability=self.ability, weapon=self.weapon_type, target=target)
        ctx.is_critical = ctx.is_critical or roll.raw >= actor.attributes.crit_roll()

        ctx.attack_roll = roll
        actor.trigger_event(EventType.ATTACK_ROLL, actor, target, ctx)

        ctx.is_hit = ctx.is_critical or ctx.attack_roll.total >= target.armor_class

        if ctx.is_critical:
            # Critical guarantees a hit -> direct damage roll with critical
            actor.log_event(f"Rolls a NATURAL {roll.raw}! Critical hit!", icon=Icon.ROLL)
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
        ctx.damage_roll = actor.damage_roll(
            damage_dice=self.damage_dice, ability=self.ability, is_critical=ctx.is_critical
        )
        ctx.damage = Damage(components=[DamageComponent(value=ctx.damage_roll.total, type=self.damage_type)])
        actor.log_event(f"Damage roll: {ctx.damage_roll.total}", icon=Icon.ROLL)

        # Apply target resistances and vulnerabilities
        ctx.damage = target.modify_incoming_damage(ctx.damage)

        # Apply actor status effects
        actor.trigger_event(EventType.APPLY_DAMAGE, actor, target, ctx)

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
            target.try_apply_condition(effect)

        return ctx

    def _fire_start_events(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        actor.trigger_event(EventType.COMBAT_START, actor, target, ctx)
        target.trigger_event(EventType.COMBAT_START, actor, target, ctx)

    def _fire_end_events(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        actor.trigger_event(EventType.COMBAT_END, actor, target, ctx)
        target.trigger_event(EventType.COMBAT_END, actor, target, ctx)

    def __str__(self) -> str:
        effects = ", ".join([str(eff) for eff in self.status_effects]) if self.status_effects else "None"
        return (
            f"- {self.id}: {self.name} — {self.description} "
            f"(Type: {self.type.value}, Category: {self.category.value}, Targeting: {self.targeting.value}, "
            f"Ability: {self.ability.value}, Damage: {self.damage_dice} {self.damage_type.value}, "
            f"Range: {self.range} m, Hits: {self.hits}, Status Effects: {effects})"
        )


class MainHandAttackAction(StandardAction, AttackAction):
    id: str = "main_hand_attack"
    name: str = "Main Hand Attack"
    description: str = "Base attack with main hand weapon."
    type: ActionType = ActionType.ATTACK

    @classmethod
    def from_weapon(cls, weapon: MeleeWeapon, *, is_two_handed: bool = False, abilities: Abilities) -> Self:
        versatile_enabled = weapon.handling == WeaponHandling.VERSATILE and is_two_handed
        damage_dice = weapon.versatile_damage if versatile_enabled else None
        damage_dice = damage_dice or weapon.damage_dice

        ability = (
            (AbilityType.STR if abilities.strength >= abilities.dexterity else AbilityType.DEX)
            if weapon.finesse
            else weapon.ability
        )

        return cls(
            description=f"Base Attack with main hand weapon {weapon.name}",
            weapon_type=weapon.weapon_type,
            targeting=weapon.targeting,
            damage_dice=damage_dice,
            damage_type=weapon.damage_type,
            ability=ability,
            range=weapon.range,
            status_effects=weapon.effects,
            metadata={
                "slot": "main_hand",
            },
        )


class OffHandAttackAction(BonusAction, AttackAction):
    id: str = "off_hand_attack"
    name: str = "Off Hand Attack"
    description: str = ""
    type: ActionType = ActionType.OFF_HAND_ATTACK

    @classmethod
    def from_weapon(cls, weapon: MeleeWeapon) -> Self:
        return cls(
            description=f"Bonus Attack with off hand weapon {weapon.name}",
            weapon_type=weapon.weapon_type,
            targeting=weapon.targeting,
            damage_dice=weapon.damage_dice,
            damage_type=weapon.damage_type,
            ability=weapon.ability,
            range=weapon.range,
            status_effects=weapon.effects,
            metadata={
                "slot": "off_hand",
            },
        )


class BonusAttackAction(BonusAction, AttackAction):
    id: str = "bonus_attack"
    name: str = "Bonus Attack"
    description: str = ""
    type: ActionType = ActionType.ATTACK


class RangedAttackAction(StandardAction, AttackAction):
    id: str = "ranged_attack"
    name: str = "Ranged Attack"
    description: str = ""
    type: ActionType = ActionType.ATTACK

    def execute(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        if actor.los_distance(target.pos) <= MELEE_RANGE:
            trait = TraitBuilder.attacker_disadvantage(source_id="ranged_attack", name="Short range Disadvantage")
            actor.register_passive(trait)

        super().execute(actor, target, ctx)

        actor.unregister_passive(feature_id=FeatureId.ATTACKER_DISADVANTAGE, source_id="ranged_attack")

    @classmethod
    def from_weapon(cls, weapon: RangedWeapon) -> Self:
        return cls(
            description=f"Ranged Attack with {weapon.name}",
            weapon_type=weapon.weapon_type,
            targeting=weapon.targeting,
            damage_dice=weapon.damage_dice,
            damage_type=weapon.damage_type,
            ability=weapon.ability,
            range=weapon.range,
            status_effects=weapon.effects,
            metadata={
                "slot": "ranged",
            },
        )
