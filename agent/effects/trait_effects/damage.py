from __future__ import annotations

from typing import TYPE_CHECKING

from agent.logs.events import LogLevel
from agent.models.constants import MELEE_RANGE, TRAIT_LOG_LEVEL
from agent.models.damage import Damage, DamageComponent, DamageType, DamageVulnerability

if TYPE_CHECKING:
    from agent.character.resolvers.base import CharacterBase
    from agent.models.context import CombatContext


def auto_crit_if_melee_effect(actor: CharacterBase, target: CharacterBase, context: CombatContext) -> None:
    if actor.los_distance(target.pos) <= MELEE_RANGE:
        context.is_critical = True
        actor.log_event(f"{actor.name} gains automatic crit against {target.name}!", log_type=TRAIT_LOG_LEVEL)


def damage_over_time_effect(target: CharacterBase, value: int, damage_type: DamageType) -> None:
    damage = Damage(components=[DamageComponent(value=value, type=damage_type)])
    damage = target.modify_incoming_damage(damage)
    target.apply_damage(damage.total)
    target.log_event(f"{target.name} suffers {damage.total} {damage_type.value} damage.", log_type=TRAIT_LOG_LEVEL)


def reflect_melee_damage_effect(
    actor: CharacterBase, target: CharacterBase, context: CombatContext, ratio: float, damage_type: DamageType
) -> None:
    has_damage = context.damage and any(c.type == damage_type for c in context.damage.components)
    if has_damage and actor.los_distance(target.pos) <= MELEE_RANGE:
        value = context.damage.total * ratio  # type: ignore[union-attr]
        damage = Damage(components=[DamageComponent(value=value, type=damage_type)])
        damage = actor.modify_incoming_damage(damage)
        actor.apply_damage(damage.total)
        target.log_event(
            f"{target.name} reflects {damage.total:.0f} {damage_type.value} damage back to {actor.name}.",
            log_type=LogLevel.DEBUG,
        )


def damage_bonus_effect(target: CharacterBase, context: CombatContext, value: int, damage_type: DamageType) -> None:
    if context.damage:
        context.damage.components.append(DamageComponent(value=value, type=damage_type, operation="add"))
        target.log_event(f"{target.name}'s attack gains {value} {damage_type.value} damage.", log_type=TRAIT_LOG_LEVEL)


def damage_multiplier_effect(
    target: CharacterBase, context: CombatContext, value: float, damage_type: DamageType
) -> None:
    if context.damage:
        context.damage.components.append(DamageComponent(value=value, type=damage_type, operation="mul"))
        target.log_event(f"{target.name}'s {damage_type.value} damage multiplied by {value}.", log_type=TRAIT_LOG_LEVEL)


def ignore_resistance_effect(
    actor: CharacterBase, target: CharacterBase, context: CombatContext, damage_type: DamageType
) -> None:
    if context.damage:
        res = target.attributes.damage_resistance(damage_type)
        if res and res.value > 0:
            context.damage.vulnerabilities.append(DamageVulnerability(value=res.value, type=damage_type))
            actor.log_event(
                f"{actor.name} ignores {target.name}'s {damage_type.value} resistance.", log_type=TRAIT_LOG_LEVEL
            )
