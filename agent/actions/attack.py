from __future__ import annotations

from typing import TYPE_CHECKING, Self

from agent.actions.base import Action, ActionCategory, ActionEconomy, ActionType
from agent.character.stats import StatType
from agent.effects.base import StatusEffect
from agent.equipment.weapons import RangedWeapon, Weapon, WeaponType
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

    def execute(self, actor: Character, target: Character) -> str:
        ctx = CombatContext(event="")

        # Attack roll
        roll = actor.attack_roll(attack_stat=self.stat, target=target)
        is_critical = roll.raw == actor.attributes.compute_crit_roll()
        is_critical = is_critical or any(eff.is_auto_crit(actor, target) for eff in target.status_effects)

        ctx.hit_roll = roll
        ctx.is_critical = is_critical

        mod = self._attack_modifier(actor)
        expr = f"{self.damage_dice}+{mod}"

        if is_critical:
            # Critical guarantees a hit -> direct damage roll with critical
            ctx.event += f" {actor.name} rolls a NATURAL 20! Critical hit!"
            droll = actor.damage_roll(expr=expr, is_critical=True)
        else:
            # Check attack roll result
            if roll.total < target.ac:
                ctx.event += f" {actor.name} misses..."
                ctx.is_hit = False
                return ctx.event

            # Damage roll
            droll = actor.damage_roll(expr=expr, is_critical=False)

        ctx.is_hit = True
        ctx.damage_roll = droll

        ctx.damage = Damage(components=[DamageComponent(value=droll.total, type=self.damage_type)])

        # Apply actor status effects (e.g. additional damage from traits)
        for effect in actor.status_effects:
            effect.on_apply_damage(actor, target, ctx)

        # Apply resistance and vulnerability modifiers
        ctx.damage = target.modify_incoming_damage(ctx.damage)

        # Apply target status effects (e.g. shield)
        for effect in target.status_effects:
            effect.on_receive_damage(actor, target, ctx)

        # Apply damage
        total_damage = ctx.damage.total
        target.apply_damage(damage=total_damage)
        ctx.event += f" {actor.name} hits {target.name} for {total_damage} damage (HP now {target.attributes.hp})."

        # Try to apply status effects
        for effect in self.status_effects:
            applied = target.try_apply_status(effect)
            if applied:
                ctx.event += f" {target.name} is {effect.type.value}."

        if not target.is_alive:
            ctx.event += f" {target.name} is defeated!"

        return ctx.event

    def _attack_modifier(self, actor: Character) -> int:
        prof_bonus = actor.proficiency_bonus if self.weapon_type in actor.proficiencies else 0
        mod = actor.stats.modifier(self.stat)
        return mod + prof_bonus


class MainHandAttackAction(AttackAction):
    id: str = "main_hand_attack"
    name: str = "Main Hand Attack"
    description: str = "Base attack with main hand weapon."
    action_type: ActionType = ActionType.MAIN_HAND_ATTACK
    category: ActionCategory = ActionCategory.STANDARD

    @classmethod
    def from_weapon(cls, weapon: Weapon) -> Self:
        return cls(
            source=weapon.name,
            description=f"Base Attack with main hand weapon: {weapon.description}",
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
            description=f"Bonus Attack with off hand weapon: {weapon.description}",
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
        if actor.action_economy.bonus_actions <= 0:
            raise ValueError("No bonus actions left")
        actor.action_economy.bonus_actions -= 1


class RangedAttackAction(AttackAction):
    id: str = "ranged_attack"
    name: str = "Ranged Attack"
    description: str = ""
    action_type: ActionType = ActionType.RANGED_ATTACK
    category: ActionCategory = ActionCategory.STANDARD

    @classmethod
    def from_weapon(cls, weapon: RangedWeapon) -> Self:
        return cls(
            source=weapon.name,
            description=f"Ranged Attack: {weapon.description}",
            weapon_type=weapon.weapon_type,
            targeting=weapon.targeting,
            damage_dice=weapon.damage_dice,
            damage_type=weapon.damage_type,
            stat=weapon.stat,
            range=weapon.range,
            status_effects=weapon.effects,
        )
