from __future__ import annotations

import math
from typing import TYPE_CHECKING

from agent.character.stats import Modifier, StatType
from agent.models.enums import Advantage, DamageType

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
            Modifier(source_id=str(id(self)), attribute=self.attr, value=Advantage.DISADVANTAGE, operation="add"))


class AttackerAdvantageOnAttackRoll(Trait):
    attr = "defense_advantage"

    def on_apply(self, target: Character) -> None:
        target.add_modifier(
            Modifier(source_id=str(id(self)), attribute=self.attr, value=Advantage.ADVANTAGE, operation="add"))


class TargetDisadvantageOnAttackRoll(Trait):
    attr = "attack_advantage"

    def on_apply(self, target: Character) -> None:
        target.add_modifier(
            Modifier(source_id=str(id(self)), attribute=self.attr, value=Advantage.DISADVANTAGE, operation="add"))


class TargetAdvantageOnAttackRoll(Trait):
    attr = "attack_advantage"

    def on_apply(self, target: Character) -> None:
        target.add_modifier(
            Modifier(source_id=str(id(self)), attribute=self.attr, value=Advantage.ADVANTAGE, operation="add"))


class DisadvantageOnSavingThrow(Trait):
    def __init__(self, stat: StatType) -> None:
        self.attr = f"{stat.name.lower()}_save_advantage"

    def on_apply(self, target: Character) -> None:
        target.add_modifier(
            Modifier(source_id=str(id(self)), attribute=self.attr, value=Advantage.DISADVANTAGE, operation="add"))


class AdvantageOnSavingThrow(Trait):
    def __init__(self, stat: StatType) -> None:
        self.attr = f"{stat.name.lower()}_save_advantage"

    def on_apply(self, target: Character) -> None:
        target.add_modifier(
            Modifier(source_id=str(id(self)), attribute=self.attr, value=Advantage.ADVANTAGE, operation="add"))


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
