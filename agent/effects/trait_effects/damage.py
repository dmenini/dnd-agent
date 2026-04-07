from __future__ import annotations

from typing import TYPE_CHECKING

from agent.character.abilities import AbilityType
from agent.effects.base import register_effect
from agent.equipment.weapons import MeleeWeapon, RangedWeapon
from agent.logs.log_event import LogLevel
from agent.models.constants import MELEE_RANGE, TRAIT_LOG_LEVEL
from agent.models.damage import Damage, DamageComponent, DamageType, DamageVulnerability
from agent.services.combat_service import CombatService
from agent.services.roll_service import RollService

if TYPE_CHECKING:
    from agent.character.character import Character
    from agent.models.context import CombatContext


@register_effect()
def auto_crit_if_melee_effect(actor: Character, target: Character, context: CombatContext) -> None:
    if actor.los_distance(target.pos) <= MELEE_RANGE:
        context.is_critical = True
        actor.log_event(f"{actor.name} gains automatic crit against {target.name}!", log_type=TRAIT_LOG_LEVEL)


@register_effect()
def damage_over_time_effect(target: Character, value: int, damage_type: DamageType) -> None:
    damage = Damage(components=[DamageComponent(value=value, type=damage_type)])
    damage = CombatService.modify_incoming_damage(target, damage)
    CombatService.apply_damage(target, damage.total)
    target.log_event(f"{target.name} suffers {damage.total} {damage_type.value} damage.", log_type=TRAIT_LOG_LEVEL)


@register_effect()
def reflect_melee_damage_effect(
    actor: Character, target: Character, context: CombatContext, ratio: float, damage_type: DamageType
) -> None:
    has_damage = context.damage and any(c.type == damage_type for c in context.damage.components)
    if has_damage and actor.los_distance(target.pos) <= MELEE_RANGE:
        value = context.damage.total * ratio  # type: ignore[union-attr]
        damage = Damage(components=[DamageComponent(value=value, type=damage_type)])
        damage = CombatService.modify_incoming_damage(actor, damage)
        CombatService.apply_damage(actor, damage.total)
        target.log_event(
            f"{target.name} reflects {damage.total:.0f} {damage_type.value} damage back to {actor.name}.",
            log_type=LogLevel.DEBUG,
        )


@register_effect()
def damage_bonus_effect(actor: Character, context: CombatContext, value: int, damage_type: DamageType) -> None:
    if context.damage:
        context.damage.components.append(DamageComponent(value=value, type=damage_type, operation="add"))
        actor.log_event(f"{actor.name}'s attack gains {value} {damage_type.value} damage.", log_type=TRAIT_LOG_LEVEL)


@register_effect()
def weapon_damage_bonus_effect(actor: Character, context: CombatContext, dice: str, damage_type: DamageType) -> None:
    """Add bonus damage from dice rolls to weapon attacks only."""
    slot = context.metadata.get("metadata", {}).get("slot")
    weapon = actor.equipment.slots.get(slot) if slot else None
    is_weapon_attack = isinstance(weapon, (MeleeWeapon, RangedWeapon))

    if context.damage and is_weapon_attack:
        result = RollService.roll(dice, character=actor).total
        context.damage.components.append(DamageComponent(value=result, type=damage_type, operation="add"))
        actor.log_event(
            f"{actor.name}'s weapon attack gains {result} {damage_type.value} damage.", log_type=TRAIT_LOG_LEVEL
        )


@register_effect()
def melee_damage_bonus_effect(actor: Character, context: CombatContext, value: int) -> None:
    slot = context.metadata.get("metadata", {}).get("slot")
    weapon = actor.equipment.slots.get(slot)
    is_melee = isinstance(weapon, MeleeWeapon) and weapon.ability == AbilityType.STR
    if is_melee:
        # Extract damage_type from the first damage effect in the action metadata
        damage_type = _extract_damage_type(context)
        damage_bonus_effect(actor, context, value=value, damage_type=damage_type)


@register_effect()
def sneak_attack_effect(actor: Character, context: CombatContext, *, dice: str) -> None:
    slot = context.metadata.get("metadata", {}).get("slot")
    is_finesse_or_ranged = False
    if slot:
        weapon = actor.equipment.slots.get(slot)
        is_finesse_or_ranged = isinstance(weapon, RangedWeapon) or (isinstance(weapon, MeleeWeapon) and weapon.finesse)
    is_first_attack = (
        actor.action_economy.last_standard_action is None and actor.action_economy.last_bonus_action is None
    )
    has_advantage = context.attack_roll and context.attack_roll.advantage is True
    if context.damage and has_advantage and is_finesse_or_ranged and is_first_attack:
        result = RollService.roll(dice, character=actor).total
        # Extract damage_type from the first damage effect in the action metadata
        damage_type = _extract_damage_type(context)
        context.damage.components.append(DamageComponent(value=result, type=damage_type, operation="add"))
        actor.log_event(f"{actor.name}'s attack gains {result} {damage_type.value} damage.", log_type=TRAIT_LOG_LEVEL)


@register_effect()
def damage_multiplier_effect(actor: Character, context: CombatContext, value: float, damage_type: DamageType) -> None:
    if context.damage:
        context.damage.components.append(DamageComponent(value=value, type=damage_type, operation="mul"))
        actor.log_event(f"{actor.name}'s {damage_type.value} damage multiplied by {value}.", log_type=TRAIT_LOG_LEVEL)


@register_effect()
def ignore_resistance_effect(
    actor: Character, target: Character, context: CombatContext, damage_type: DamageType
) -> None:
    if context.damage:
        res = target.attributes.damage_resistance(damage_type)
        if res and res.value > 0:
            context.damage.vulnerabilities.append(DamageVulnerability(value=res.value, type=damage_type))
            actor.log_event(
                f"{actor.name} ignores {target.name}'s {damage_type.value} resistance.", log_type=TRAIT_LOG_LEVEL
            )


def _extract_damage_type(context: CombatContext) -> DamageType:
    damage_type = context.metadata.get("damage_type")
    if not damage_type:
        effects = context.metadata.get("effects", [])
        for effect in effects:
            if effect.get("type") == "damage":
                damage_type = effect.get("damage_type")
                break
    if not damage_type:
        msg = "Damage type not found in context"
        raise ValueError(msg)

    return damage_type
