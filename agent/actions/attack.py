from __future__ import annotations

from typing import Self, TYPE_CHECKING

from agent.actions.base import Action, ActionCategory, ActionType
from agent.character.resources import ActionEconomy
from agent.character.stats import StatType
from agent.effects.base import StatusEffect
from agent.equipment.weapons import RangedWeapon, Weapon, WeaponType
from agent.logs.events import Icon
from agent.models.context import CombatContext
from agent.models.damage import Damage, DamageComponent, DamageType
from agent.models.enums import TargetingType

if TYPE_CHECKING:
    from agent.character.character import Character


class AttackAction(Action):
    source: str
    targeting: TargetingType
    damage_dice: str
    damage_type: DamageType
    weapon_type: WeaponType
    stat: StatType
    range: float
    status_effects: list[StatusEffect] = []

    def execute(self, actor: Character, target: Character) -> None:
        ctx = CombatContext()

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
            actor.log_event(f"Attack roll: {roll.total} vs AC {target.armor_class}", icon=Icon.ROLL)
            if ctx.is_hit:
                actor.log_event("Attack roll passed → Hits target!", icon=Icon.ATTACK)
            else:
                actor.log_event("Attack roll failed → Target missed...", icon=Icon.ATTACK)

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
        for effect in actor.status_effects:
            effect.on_apply_damage(actor, target, ctx)

        # Apply target resistances and vulnerabilities
        ctx.damage = target.modify_incoming_damage(ctx.damage)

        # Apply target status effects
        for effect in target.status_effects:
            effect.on_receive_damage(actor, target, ctx)

        # Apply damage
        total_damage = ctx.damage.total
        target.apply_damage(damage=total_damage)
        actor.log_event(f"Damage dealt: {total_damage} ({ctx.damage})", icon=Icon.DAMAGE)
        target.log_event(f"{target.name}: {target.attributes.hp}/{target.max_hp} HP")

        if not target.is_alive:
            target.log_event(f"{target.name} is defeated", icon=Icon.DEATH)
            return ctx

        # Try to apply status effects
        for effect in self.status_effects:
            target.try_apply_status(effect)

        return ctx

    def _attack_modifier(self, actor: Character) -> int:
        prof_bonus = actor.proficiency_bonus if self.weapon_type in actor.proficiencies else 0
        mod = actor.attributes.stat_modifier(self.stat)
        return mod + prof_bonus

    def _fire_start_events(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        for eff in actor.status_effects:
            eff.on_combat_start(actor, target, ctx)

        for eff in target.status_effects:
            eff.on_combat_start(actor, target, ctx)

    def _fire_end_events(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        for eff in actor.status_effects:
            eff.on_combat_end(actor, target, ctx)

        for eff in target.status_effects:
            eff.on_combat_end(actor, target, ctx)


class MainHandAttackAction(AttackAction):
    id: str = "main_hand_attack"
    name: str = "Main Hand Attack"
    description: str = "Base attack with main hand weapon."
    action_type: ActionType = ActionType.ATTACK
    category: ActionCategory = ActionCategory.STANDARD

    @classmethod
    def from_weapon(cls, weapon: Weapon) -> Self:
        return cls(
            source=weapon.name,
            description=f"Base Attack with main hand weapon {weapon.name}",
            weapon_type=weapon.weapon_type,
            targeting=weapon.targeting,
            damage_dice=weapon.damage_dice,
            damage_type=weapon.damage_type,
            stat=weapon.stat,
            range=weapon.range,
            status_effects=weapon.effects,
        )


class OffHandAttackAction(AttackAction):
    id: str = "off_hand_attack"
    name: str = "Off Hand Attack"
    description: str = ""
    action_type: ActionType = ActionType.OFF_HAND_ATTACK
    category: ActionCategory = ActionCategory.BONUS

    @classmethod
    def from_weapon(cls, weapon: Weapon) -> Self:
        return cls(
            source=weapon.name,
            description=f"Bonus Attack with off hand weapon {weapon.name}",
            weapon_type=weapon.weapon_type,
            targeting=weapon.targeting,
            damage_dice=weapon.damage_dice,
            damage_type=weapon.damage_type,
            stat=weapon.stat,
            range=weapon.range,
            status_effects=weapon.effects,
        )

    def is_available(self, action_economy: ActionEconomy) -> bool:
        return action_economy.bonus_actions > 0

    def finalize(self, actor: Character) -> None:
        """Consume bonus point."""
        actor.action_economy.can_use_bonus(self.action_type)


class RangedAttackAction(AttackAction):
    id: str = "ranged_attack"
    name: str = "Ranged Attack"
    description: str = ""
    action_type: ActionType = ActionType.ATTACK
    category: ActionCategory = ActionCategory.STANDARD

    @classmethod
    def from_weapon(cls, weapon: RangedWeapon) -> Self:
        return cls(
            source=weapon.name,
            description=f"Ranged Attack with {weapon.name}",
            weapon_type=weapon.weapon_type,
            targeting=weapon.targeting,
            damage_dice=weapon.damage_dice,
            damage_type=weapon.damage_type,
            stat=weapon.stat,
            range=weapon.range,
            status_effects=weapon.effects,
        )
