from __future__ import annotations

import math
from typing import TYPE_CHECKING

from pydantic import BaseModel

from agent.character.attributes import Modifier
from agent.character.stats import StatType
from agent.models.damage import DamageType
from agent.models.enums import Advantage

if TYPE_CHECKING:
    from agent.character.character import Character

MELEE_RANGE = 5


class Trait(BaseModel):
    def on_expire(self, target: Character) -> None:
        target.remove_modifier(str(id(self)))


class AttackerDisadvantageOnAttackRoll(Trait):
    def on_apply(self, target: Character) -> None:
        attr = "advantage.defense"
        target.add_modifier(
            Modifier(source_id=str(id(self)), attribute=attr, value=Advantage.DISADVANTAGE, operation="add")
        )


class AttackerAdvantageOnAttackRoll(Trait):
    def on_apply(self, target: Character) -> None:
        attr = "advantage.defense"
        target.add_modifier(
            Modifier(source_id=str(id(self)), attribute=attr, value=Advantage.ADVANTAGE, operation="add")
        )


class TargetDisadvantageOnAttackRoll(Trait):
    def on_apply(self, target: Character) -> None:
        attr = "advantage.attack"
        target.add_modifier(
            Modifier(source_id=str(id(self)), attribute=attr, value=Advantage.DISADVANTAGE, operation="add")
        )


class TargetAdvantageOnAttackRoll(Trait):
    def on_apply(self, target: Character) -> None:
        attr = "advantage.attack"
        target.add_modifier(
            Modifier(source_id=str(id(self)), attribute=attr, value=Advantage.ADVANTAGE, operation="add")
        )


class DisadvantageOnSavingThrow(Trait):
    stat: StatType

    def on_apply(self, target: Character) -> None:
        attr = f"save_advantage.{self.stat.name.lower()}"
        target.add_modifier(
            Modifier(source_id=str(id(self)), attribute=attr, value=Advantage.DISADVANTAGE, operation="add")
        )


class AdvantageOnSavingThrow(Trait):
    stat: StatType

    def on_apply(self, target: Character) -> None:
        attr = f"save_advantage.{self.stat.name.lower()}"
        target.add_modifier(
            Modifier(source_id=str(id(self)), attribute=attr, value=Advantage.ADVANTAGE, operation="add")
        )


class FailOnSavingThrow(Trait):
    stat: StatType

    def on_apply(self, target: Character) -> None:
        attr = f"save_autofail.{self.stat.name.lower()}"
        target.add_modifier(Modifier(source_id=str(id(self)), attribute=attr, value=True, operation="set"))


class SpeedMultiplier(Trait):
    value: float

    def on_apply(self, target: Character) -> None:
        attr = "speed"
        target.add_modifier(Modifier(source_id=str(id(self)), attribute=attr, value=self.value, operation="mul"))


class SpeedBonus(Trait):
    value: float

    def on_apply(self, target: Character) -> None:
        attr = "speed"
        target.add_modifier(Modifier(source_id=str(id(self)), attribute=attr, value=self.value, operation="add"))


class ACBonus(Trait):
    value: int

    def on_apply(self, target: Character) -> None:
        attr = "ac"
        target.add_modifier(Modifier(source_id=str(id(self)), attribute=attr, value=self.value, operation="add"))


class AutoCritIfMelee(Trait):
    def is_auto_crit(self, actor: Character, target: Character) -> bool:
        return actor.distance(target.pos) <= MELEE_RANGE


class CriticalRollBonus(Trait):
    value: int

    def on_apply(self, target: Character) -> None:
        attr = "crit_roll"
        target.add_modifier(Modifier(source_id=str(id(self)), attribute=attr, value=-self.value, operation="add"))


class DamageOverTime(Trait):
    damage: int
    damage_type: DamageType

    def on_turn_end(self, target: Character) -> None:
        target.apply_damage(damage=self.damage, damage_type=self.damage_type)


class CannotMove(Trait):
    def on_turn_start(self, target: Character) -> None:
        target.action_economy.movement_available = False  # Cannot move


class CannotAct(Trait):
    def on_turn_start(self, target: Character) -> None:
        target.action_economy.standard_actions = -1
        target.action_economy.bonus_actions = -1
        target.action_economy.reaction_available = False


class ExtraActions(Trait):
    value: int = 1

    def on_turn_start(self, target: Character) -> None:
        if target.action_economy.standard_actions > 0:
            target.action_economy.standard_actions += self.value


class HalfActions(Trait):
    def on_turn_start(self, target: Character) -> None:
        # TODO: Should be limited to attacks
        if target.action_economy.standard_actions > 1:
            target.action_economy.standard_actions = math.ceil(target.action_economy.standard_actions / 2)


class LifeSteal(Trait):
    ratio: float = 0.1

    def on_apply_damage(self, actor: Character, _: Character, damage: int, dtype: DamageType) -> None:  # noqa: ARG002
        heal = int(damage * self.ratio)
        actor.heal(heal)


class DamageBonus(Trait):
    value: int
    damage_type: DamageType

    def on_apply_damage(self, actor: Character, target: Character, damage: int, dtype: DamageType) -> int:  # noqa: ARG002
        return damage + self.value


class DamageMultiplier(Trait):
    value: int
    damage_type: DamageType

    def on_apply_damage(self, actor: Character, target: Character, damage: int, dtype: DamageType) -> int:  # noqa: ARG002
        return int(damage * self.value)


class IgnoreResistance(Trait):
    damage_type: DamageType

    def on_apply_damage(self, _: Character, target: Character, damage: int, dtype: DamageType) -> int:
        if dtype == self.damage_type and target.attributes.compute_resistance(self.damage_type) > 0:
            return damage  # skip resistance reduction
        return damage


class Resistance(Trait):
    value: float
    damage_type: DamageType

    def on_apply(self, target: Character) -> None:
        attr = f"resistance.{self.damage_type.value}"
        target.add_modifier(Modifier(source_id=str(id(self)), attribute=attr, value=self.value, operation="mul"))


class Immunity(Trait):
    damage_type: DamageType

    def on_apply(self, target: Character) -> None:
        attr = f"resistance.{self.damage_type.value}"
        target.add_modifier(Modifier(source_id=str(id(self)), attribute=attr, value=1.0, operation="mul"))


class SpellResistance(Trait):
    # TODO: Implement check in spell action
    def on_apply(self, target: Character) -> None:
        attr = "advantage.spell_save"
        target.add_modifier(
            Modifier(source_id=str(id(self)), attribute=attr, value=Advantage.ADVANTAGE, operation="add")
        )


class StealthDisadvantage(Trait):
    # TODO: Implement check
    def on_apply(self, target: Character) -> None:
        attr = "advantage.stealth"
        target.add_modifier(
            Modifier(source_id=str(id(self)), attribute=attr, value=Advantage.DISADVANTAGE, operation="add")
        )


class Regeneration(Trait):
    value: int

    def on_turn_start(self, target: Character) -> None:
        target.heal(self.value)
