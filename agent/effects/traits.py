from __future__ import annotations

import math
from typing import TYPE_CHECKING

from agent.character.stats import Modifier, StatType
from agent.equipment.weapons import DamageType
from agent.models.enums import Advantage

if TYPE_CHECKING:
    from agent.character.character import Character

MELEE_RANGE = 5


class Trait:
    def on_expire(self, target: Character) -> None:
        target.remove_modifier(str(id(self)))


class AttackerDisadvantageOnAttackRoll(Trait):
    attr = "defense_advantage"

    def on_apply(self, target: Character) -> None:
        target.add_modifier(
            Modifier(source_id=str(id(self)), attribute=self.attr, value=Advantage.DISADVANTAGE, operation="add")
        )


class AttackerAdvantageOnAttackRoll(Trait):
    attr = "defense_advantage"

    def on_apply(self, target: Character) -> None:
        target.add_modifier(
            Modifier(source_id=str(id(self)), attribute=self.attr, value=Advantage.ADVANTAGE, operation="add")
        )


class TargetDisadvantageOnAttackRoll(Trait):
    attr = "attack_advantage"

    def on_apply(self, target: Character) -> None:
        target.add_modifier(
            Modifier(source_id=str(id(self)), attribute=self.attr, value=Advantage.DISADVANTAGE, operation="add")
        )


class TargetAdvantageOnAttackRoll(Trait):
    attr = "attack_advantage"

    def on_apply(self, target: Character) -> None:
        target.add_modifier(
            Modifier(source_id=str(id(self)), attribute=self.attr, value=Advantage.ADVANTAGE, operation="add")
        )


class DisadvantageOnSavingThrow(Trait):
    def __init__(self, stat: StatType) -> None:
        self.attr = f"{stat.name.lower()}_save_advantage"

    def on_apply(self, target: Character) -> None:
        target.add_modifier(
            Modifier(source_id=str(id(self)), attribute=self.attr, value=Advantage.DISADVANTAGE, operation="add")
        )


class AdvantageOnSavingThrow(Trait):
    def __init__(self, stat: StatType) -> None:
        self.attr = f"{stat.name.lower()}_save_advantage"

    def on_apply(self, target: Character) -> None:
        target.add_modifier(
            Modifier(source_id=str(id(self)), attribute=self.attr, value=Advantage.ADVANTAGE, operation="add")
        )


class FailOnSavingThrow(Trait):
    def __init__(self, stat: StatType) -> None:
        self.attr = f"{stat.name.lower()}_save_autofail"

    def on_apply(self, target: Character) -> None:
        target.add_modifier(Modifier(source_id=str(id(self)), attribute=self.attr, value=True, operation="set"))


class SpeedBonus(Trait):
    attr = "speed"

    def __init__(self, mult: float) -> None:
        self.mult = mult

    def on_apply(self, target: Character) -> None:
        target.add_modifier(Modifier(source_id=str(id(self)), attribute=self.attr, value=self.mult, operation="mul"))


class ACBonus(Trait):
    attr = "ac"

    def __init__(self, val: int) -> None:
        self.val = val

    def on_apply(self, target: Character) -> None:
        target.add_modifier(Modifier(source_id=str(id(self)), attribute=self.attr, value=self.val, operation="add"))


class AutoCritIfMelee(Trait):
    def is_auto_crit(self, actor: Character, target: Character) -> bool:
        return actor.distance(target.pos) <= MELEE_RANGE


class DamageOverTime(Trait):
    def __init__(self, damage: int, dtype: DamageType) -> None:
        self.damage = damage
        self.dtype = dtype

    def on_turn_end(self, target: Character) -> None:
        target.apply_damage(damage=self.damage, damage_type=self.dtype)


class CannotMove(Trait):
    def on_turn_start(self, target: Character) -> None:
        target.action_economy.movement_available = False  # Cannot move


class CannotAct(Trait):
    def on_turn_start(self, target: Character) -> None:
        target.action_economy.standard_actions = -1
        target.action_economy.bonus_actions = -1
        target.action_economy.reaction_available = False


class ExtraAction(Trait):
    def on_turn_start(self, target: Character) -> None:
        if target.action_economy.standard_actions > 0:
            target.action_economy.standard_actions += 1


class HalveActions(Trait):
    def on_turn_start(self, target: Character) -> None:
        if target.action_economy.standard_actions > 1:
            target.action_economy.standard_actions = math.ceil(target.action_economy.standard_actions / 2)


class BonusDamage(Trait):
    def __init__(self, amount: int, dtype: DamageType) -> None:
        self.amount = amount
        self.dtype = dtype

    def on_apply_damage(self, actor: Character, target: Character, damage: int, dtype: DamageType) -> int:
        return damage + self.amount


class DamageMultiplier(Trait):
    def __init__(self, mult: float) -> None:
        self.mult = mult

    def on_apply_damage(self, actor: Character, target: Character, damage: int, dtype: DamageType) -> int:
        return int(damage * self.mult)


class ExtraAttack(Trait):
    def __init__(self, count: int = 1) -> None:
        self.count = count

    def on_turn_start(self, target: Character) -> None:
        target.action_economy.extra_attacks += self.count


class IgnoreResistance(Trait):
    def __init__(self, dtype: DamageType) -> None:
        self.dtype = dtype

    def on_apply_damage(self, actor: Character, target: Character, damage: int, dtype: DamageType) -> int:
        if dtype == self.dtype and target.has_resistance(dtype):
            return damage  # skip resistance reduction
        return damage


class CriticalRollBonus(Trait):
    attr = "crit_roll"

    def __init__(self, bonus: int) -> None:
        self.bonus = bonus  # e.g. reduces crit threshold from 20 to 19

    def on_apply(self, target: Character) -> None:
        target.add_modifier(
            Modifier(source_id=str(id(self)), attribute=self.attr, value=-self.bonus, operation="add")
        )


class LifeSteal(Trait):
    def __init__(self, ratio: float = 0.1) -> None:
        self.ratio = ratio

    def on_apply_damage(self, actor: Character, _: Character, damage: int, dtype: DamageType) -> None:
        heal = int(damage * self.ratio)
        actor.heal(heal)


class Resistance(Trait):
    def __init__(self, dtype: DamageType, reduction: float = 0.5) -> None:
        self.dtype = dtype
        self.reduction = reduction

    def on_receive_damage(self, _: Character, damage: int, dtype: DamageType) -> int:
        if dtype == self.dtype:
            return int(damage * self.reduction)
        return damage


class Immunity(Trait):
    def __init__(self, dtype: DamageType) -> None:
        self.dtype = dtype

    # TODO: This should bypass the other damage modifiers
    def on_receive_damage(self, _: Character, damage: int, dtype: DamageType) -> int:
        return 0 if dtype == self.dtype else damage


class SpellResistance(Trait):
    attr = "spell_save_advantage"

    # TODO: Implement check in spell action
    def on_apply(self, target: Character) -> None:
        target.add_modifier(
            Modifier(source_id=str(id(self)), attribute=self.attr, value=Advantage.ADVANTAGE,
                     operation="add")
        )


class StealthDisadvantage(Trait):
    attr = "stealth_advantage"

    def on_apply(self, target: Character) -> None:
        target.add_modifier(
            Modifier(source_id=str(id(self)), attribute=self.attr, value=Advantage.DISADVANTAGE,
                     operation="add")
        )


class Regeneration(Trait):
    def __init__(self, amount: int) -> None:
        self.amount = amount

    def on_turn_start(self, target: Character) -> None:
        target.heal(self.amount)
