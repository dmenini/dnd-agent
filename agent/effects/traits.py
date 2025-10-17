from __future__ import annotations

import math
import uuid
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, PrivateAttr

from agent.character.attributes import Modifier
from agent.character.stats import StatType
from agent.models.context import CombatContext
from agent.models.damage import Damage, DamageComponent, DamageType, DamageVulnerability

if TYPE_CHECKING:
    from agent.character.character import Character

MELEE_RANGE = 5


class Trait(BaseModel):
    _id: str = PrivateAttr(default_factory=lambda: str(uuid.uuid4()))

    def on_expire(self, target: Character) -> None:
        target.remove_modifier(self._id)


class AttackerDisadvantageOnAttackRoll(Trait):
    def on_apply(self, target: Character) -> None:
        attr = "disadvantage.defense"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class AttackerAdvantageOnAttackRoll(Trait):
    def on_apply(self, target: Character) -> None:
        attr = "advantage.defense"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class TargetDisadvantageOnAttackRoll(Trait):
    def on_apply(self, target: Character) -> None:
        attr = "disadvantage.attack"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class TargetAdvantageOnAttackRoll(Trait):
    def on_apply(self, target: Character) -> None:
        attr = "advantage.attack"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class DisadvantageOnSavingThrow(Trait):
    stat: StatType

    def on_apply(self, target: Character) -> None:
        attr = f"save_disadvantage.{self.stat.name.lower()}"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class AdvantageOnSavingThrow(Trait):
    stat: StatType

    def on_apply(self, target: Character) -> None:
        attr = f"save_advantage.{self.stat.name.lower()}"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class FailOnSavingThrow(Trait):
    stat: StatType

    def on_apply(self, target: Character) -> None:
        attr = f"save_autofail.{self.stat.name.lower()}"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class SpeedMultiplier(Trait):
    value: float = Field(ge=0)

    def on_apply(self, target: Character) -> None:
        attr = "speed"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=self.value, operation="mul"))


class SpeedBonus(Trait):
    value: float

    def on_apply(self, target: Character) -> None:
        attr = "speed"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=self.value, operation="add"))


class ACBonus(Trait):
    value: int

    def on_apply(self, target: Character) -> None:
        attr = "ac"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=self.value, operation="add"))


class AutoCritIfMelee(Trait):
    def is_auto_crit(self, actor: Character, target: Character) -> bool:
        return actor.distance(target.pos) <= MELEE_RANGE


class CriticalRollBonus(Trait):
    value: int

    def on_apply(self, target: Character) -> None:
        attr = "crit_roll_bonus"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=-self.value, operation="add"))


class DamageOverTime(Trait):
    value: int
    damage_type: DamageType

    def on_turn_end(self, target: Character) -> None:
        # TODO: Should it bypass the resistances? Maybe it's more deterministic as the resistances may have expired
        damage = Damage(components=[DamageComponent(value=self.value, type=self.damage_type)])
        damage = target.modify_incoming_damage(damage)
        target.apply_damage(damage=damage.total)


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


class ReflectMeleeDamage(Trait):
    value: int
    damage_type: DamageType

    def on_receive_damage(self, actor: Character, target: Character, _: CombatContext) -> None:
        if actor.distance(target.pos) <= MELEE_RANGE:
            damage = Damage(components=[DamageComponent(value=self.value, type=self.damage_type)])
            damage = actor.modify_incoming_damage(damage)
            actor.apply_damage(damage=damage.total)


class LifeSteal(Trait):
    ratio: float = 0.1

    def on_apply_damage(self, actor: Character, _: Character, context: CombatContext) -> None:
        if context.damage is not None:
            heal = math.ceil(context.damage.total * self.ratio)
            actor.heal(heal)


class DamageBonus(Trait):
    value: int
    damage_type: DamageType

    def on_apply_damage(self, actor: Character, target: Character, context: CombatContext) -> None:  # noqa: ARG002
        if context.damage is not None:
            context.damage.components.append(DamageComponent(value=self.value, type=self.damage_type, operation="add"))


class DamageMultiplier(Trait):
    value: int = Field(ge=0)
    damage_type: DamageType

    def on_apply_damage(self, actor: Character, target: Character, context: CombatContext) -> None:  # noqa: ARG002
        if context.damage is not None:
            context.damage.components.append(DamageComponent(value=self.value, type=self.damage_type, operation="mul"))


class IgnoreResistance(Trait):
    damage_type: DamageType

    def on_apply_damage(self, _: Character, target: Character, context: CombatContext) -> None:
        res = target.attributes.compute_resistance(self.damage_type)
        if res.value > 0 and context.damage is not None:
            # Balance the resistance by adding the opposite vulnerability component
            context.damage.vulnerabilities.append(DamageVulnerability(value=res.value, type=self.damage_type))


class Resistance(Trait):
    value: float
    damage_type: DamageType

    def on_apply(self, target: Character) -> None:
        attr = f"resistance.{self.damage_type.value}"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=self.value, operation="add"))


class Immunity(Trait):
    damage_type: DamageType

    def on_apply(self, target: Character) -> None:
        attr = f"resistance.{self.damage_type.value}"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=1.0, operation="add"))


class Vulnerability(Trait):
    value: float
    damage_type: DamageType

    def on_apply(self, target: Character) -> None:
        attr = f"vulnerability.{self.damage_type.value}"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=self.value, operation="add"))


class SpellResistance(Trait):
    # TODO: Implement check in spell action
    def on_apply(self, target: Character) -> None:
        attr = "advantage.spell_save"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class StealthDisadvantage(Trait):
    # TODO: Implement check
    def on_apply(self, target: Character) -> None:
        attr = "disadvantage.stealth"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class Regeneration(Trait):
    value: int

    def on_turn_start(self, target: Character) -> None:
        target.heal(self.value)
