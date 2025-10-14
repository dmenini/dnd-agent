from __future__ import annotations

from typing import TYPE_CHECKING, Self

from agent.actions.base import Action, ActionCategory, ActionEconomy, ActionType
from agent.effects.base import EffectType, StatusEffect
from agent.mechanics.dice_roller import DiceRoller
from agent.models.enums import (
    DamageType,
    StatType,
    TargetingType,
    WeaponType,
)

if TYPE_CHECKING:
    from agent.models.character import Character
    from agent.models.weapons import RangedWeapon, Weapon

ATTACK_ROLL_EXPR = "1d20"


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
        dice = DiceRoller()
        event = ""

        # 1. Compute actor advantage
        advantage = 1 if actor.stats.advantage(self.stat) else 0
        disadvantage = 0

        # 2. Collect modifiers from target status effects
        for effect in target.status_effects:
            adv = effect.on_attack_roll(actor, target)
            if adv is True:
                advantage += 1
                event += f" {target.name} is {effect.type.value}, attack at advantage."
            elif adv is False:
                disadvantage += 1
                event += f" {target.name} is {effect.type.value}, attack at disadvantage."

        if advantage > disadvantage:
            final_advantage = True
        elif disadvantage > advantage:
            final_advantage = False
        else:
            final_advantage = None  # cancel out

        # 4. Attack roll
        roll = dice.roll_with_context(dice_expression=ATTACK_ROLL_EXPR, advantage=final_advantage)
        if roll.total < target.ac:
            event += f" {actor.name} misses..."
            return event

        is_critical = roll.raw == dice.sides(ATTACK_ROLL_EXPR)

        # 5. Damage roll
        mod = self._attack_modifier(actor)
        expr = self.damage_dice + (f"+{mod}" if mod >= 0 else f"-{mod}")
        roll = dice.roll_with_context(dice_expression=expr, advantage=final_advantage)

        damage = roll.total
        melee = {ActionType.MAIN_HAND_ATTACK, ActionType.OFF_HAND_ATTACK}
        if is_critical or (target.has_effect(EffectType.PARALYZED) and self.action_type in melee):
            damage = roll.raw * self._crit_multiplier(actor) + mod
            event += f" {actor.name} rolls a NATURAL 20! Critical hit!"

        # 6. Let status effects modify outgoing damage
        damage = actor.modify_outgoing_damage(target, damage)

        # 7. Let target status effects modify incoming damage
        damage = target.modify_incoming_damage(damage)

        # 8. Apply damage
        target.apply_damage(damage=damage)
        event += f" {actor.name} hits {target.name} for {damage} damage (HP now {target.attributes.current_hp})."

        # 9. Apply status effect
        for effect in self.status_effects:
            applied = effect.try_apply(target)
            if applied:
                event += f" {target.name} is {effect.type.value}."

        if not target.is_alive:
            event += f" {target.name} is defeated!"

        return event

    def _attack_modifier(self, actor: Character) -> int:
        prof_bonus = actor.proficiency_bonus if self.weapon_type in actor.proficiencies else 0
        mod = actor.stats.modifier(self.stat)
        return mod + prof_bonus

    def _crit_multiplier(self, actor: Character) -> int:
        return actor.attributes.base_crit_multiplier


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
            status_effects=weapon.status_effects,
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
            status_effects=weapon.status_effects,
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
            status_effects=weapon.status_effects,
        )
