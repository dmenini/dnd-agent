from __future__ import annotations

from typing import TYPE_CHECKING

from agent.character.abilities import AbilityType
from agent.equipment.weapons import MeleeWeapon, RangedWeapon
from agent.logs.log_event import LogLevel
from agent.models.constants import MELEE_RANGE, TRAIT_LOG_LEVEL
from agent.models.damage import Damage, DamageComponent, DamageType, DamageVulnerability

if TYPE_CHECKING:
    from agent.character.character import Character
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


def damage_bonus_effect(actor: CharacterBase, context: CombatContext, value: int, damage_type: DamageType) -> None:
    if context.damage:
        context.damage.components.append(DamageComponent(value=value, type=damage_type, operation="add"))
        actor.log_event(f"{actor.name}'s attack gains {value} {damage_type.value} damage.", log_type=TRAIT_LOG_LEVEL)


def melee_damage_bonus_effect(actor: CharacterBase, context: CombatContext, value: int) -> None:
    slot = context.metadata.get("metadata", {}).get("slot")
    weapon = actor.equipment_slots.get(slot)
    is_melee = isinstance(weapon, MeleeWeapon) and weapon.ability == AbilityType.STR
    if is_melee:
        damage_bonus_effect(actor, context, value=value, damage_type=context.metadata["damage_type"])


def sneak_attack_effect(actor: Character, context: CombatContext, *, dice: str) -> None:
    slot = context.metadata.get("metadata", {}).get("slot")
    is_finesse_or_ranged = False
    if slot:
        weapon = actor.equipment_slots.get(slot)
        is_finesse_or_ranged = isinstance(weapon, RangedWeapon) or (isinstance(weapon, MeleeWeapon) and weapon.finesse)
    is_first_attack = (
        actor.action_economy.last_standard_action is None and actor.action_economy.last_bonus_action is None
    )
    has_advantage = context.attack_roll and context.attack_roll.advantage is True
    if context.damage and has_advantage and is_finesse_or_ranged and is_first_attack:
        result = actor.roll(dice).total
        damage_type = context.metadata["damage_type"]
        context.damage.components.append(DamageComponent(value=result, type=damage_type, operation="add"))
        actor.log_event(f"{actor.name}'s attack gains {result} {damage_type.value} damage.", log_type=TRAIT_LOG_LEVEL)


def damage_multiplier_effect(
    actor: CharacterBase, context: CombatContext, value: float, damage_type: DamageType
) -> None:
    if context.damage:
        context.damage.components.append(DamageComponent(value=value, type=damage_type, operation="mul"))
        actor.log_event(f"{actor.name}'s {damage_type.value} damage multiplied by {value}.", log_type=TRAIT_LOG_LEVEL)


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
