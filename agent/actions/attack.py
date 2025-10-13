from __future__ import annotations

from typing import TYPE_CHECKING, Self

from agent.actions.base import Action, ActionEconomy
from agent.mechanics.dice_roller import DiceRoller
from agent.models.enums import (
    ActionCategory,
    ActionType,
    ConditionType,
    DamageType,
    SpellLevel,
    StatType,
    TargetingType,
    WeaponType,
)

if TYPE_CHECKING:
    from agent.models.character import Character
    from agent.models.weapons import RangedWeapon, Spell, Weapon

ATTACK_ROLL_EXPR = "1d20"


class AttackAction(Action):
    source: str
    targeting: TargetingType
    damage_dice: str
    damage_type: DamageType
    weapon_type: WeaponType
    stat: StatType
    range: float

    def execute(self, actor: Character, target: Character) -> str:
        dice = DiceRoller()
        event = ""

        # 1. Compute attacker advantage
        adv_from_actor = actor.stats.advantage(self.stat)
        adv_from_target = None

        # 2. Check if target is dodging
        if target.has_effect(ConditionType.DODGING):
            adv_from_target = False
            event += f" {target.name} is dodging, attack at disadvantage."

        # 3. Resolve advantage/disadvantage interaction
        # True + False → None (they cancel)
        if adv_from_actor is True and adv_from_target is False:
            final_advantage = None
        else:
            # If either gives advantage/disadvantage, prefer that one
            final_advantage = adv_from_actor if adv_from_actor is not None else adv_from_target

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

        if is_critical:
            damage = roll.raw * self._crit_multiplier(actor) + mod
            event += f" {actor.name} rolls a NATURAL 20! Critical hit!"
        else:
            damage = roll.total
            event += f" {actor.name} rolls {roll.total} to hit."

        # 6. Apply damage
        target.apply_damage(damage=damage)
        event += f" {actor.name} hits {target.name} for {damage} damage (HP now {target.attributes.current_hp})."

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
            weapon_type=weapon.weapon_type,
            targeting=weapon.targeting,
            damage_dice=weapon.damage_dice,
            damage_type=weapon.damage_type,
            stat=weapon.stat,
            range=weapon.range,
        )


class OffHandAttackAction(AttackAction):
    id: str = "off_hand_attack"
    name: str = "Off Hand Attack"
    description: str = "Bonus attack with off hand weapon."
    action_type: ActionType = ActionType.OFF_HAND_ATTACK
    category: ActionCategory = ActionCategory.BONUS

    @classmethod
    def from_weapon(cls, weapon: Weapon) -> Self:
        return cls(
            source=weapon.name,
            weapon_type=weapon.weapon_type,
            targeting=weapon.targeting,
            damage_dice=weapon.damage_dice,
            damage_type=weapon.damage_type,
            stat=weapon.stat,
            range=weapon.range,
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
    description: str = "Base attack with ranged weapon."
    action_type: ActionType = ActionType.RANGED_ATTACK
    category: ActionCategory = ActionCategory.STANDARD

    @classmethod
    def from_weapon(cls, weapon: RangedWeapon) -> Self:
        return cls(
            source=weapon.name,
            weapon_type=weapon.weapon_type,
            targeting=weapon.targeting,
            damage_dice=weapon.damage_dice,
            damage_type=weapon.damage_type,
            stat=weapon.stat,
            range=weapon.range,
        )


class SpellAction(AttackAction):
    id: str = "cast_spell"
    name: str = "Cast Spell"
    description: str = "Cast spell."
    action_type: ActionType = ActionType.SPELL
    category: ActionCategory = ActionCategory.STANDARD
    level: SpellLevel

    @classmethod
    def from_spell(cls, spell: Spell) -> Self:
        return cls(
            id=f"cast_{spell.name.lower().replace(' ', '_')}",
            name=f"Cast {spell.name}",
            description=spell.description,
            source=spell.name,
            action_type=ActionType.AOE_SPELL if spell.targeting == TargetingType.AREA else ActionType.SPELL,
            weapon_type=WeaponType.SPELL,
            category=spell.casting_time,
            targeting=spell.targeting,
            damage_dice=spell.damage_dice,
            damage_type=spell.damage_type,
            stat=spell.stat,
            range=spell.range,
            level=spell.level,
        )

    def finalize(self, actor: Character) -> None:
        """Consume action point and spell slot."""
        super().finalize(actor)
        actor.spell_slots.consume(self.level)
