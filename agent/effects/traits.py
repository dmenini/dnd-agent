from __future__ import annotations

import math
import uuid
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, PrivateAttr

from agent.actions.base import ActionCategory, ActionType
from agent.character.modifier import Modifier
from agent.character.resources import ActionExtension
from agent.character.stats import StatType
from agent.models.context import CombatContext
from agent.models.damage import Damage, DamageComponent, DamageType, DamageVulnerability

if TYPE_CHECKING:
    from agent.character.character import Character

MELEE_RANGE = 5


class Priority:
    HIGH: int = -100  # Execute first
    MEDIUM: int = 0
    LOW: int = 100  # Execute last


class Trait(BaseModel):
    _id: str = PrivateAttr(default_factory=lambda: str(uuid.uuid4()))
    _priority: int = PrivateAttr(default_factory=lambda: Priority.MEDIUM)

    @property
    def priority(self) -> int:
        return self._priority

    def on_apply(self, target: Character) -> None:
        """Call when the effect is first applied."""

    def on_expire(self, target: Character) -> None:
        """Call when the effect is first applied."""
        target.remove_modifier(self._id)

    def on_turn_start(self, target: Character) -> None:
        """Call at the start of the target's turn."""

    def on_turn_end(self, target: Character) -> None:
        """Call at the end of the target's turn."""

    def on_receive_damage(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        """Modify damage taken."""

    def on_apply_damage(self, actor: Character, target: Character, ctx: CombatContext) -> None:
        """Modify outgoing damage."""

    def is_auto_crit(self, actor: Character, target: Character) -> bool:  # noqa: ARG002
        """Modify crit chance."""
        return False


class AttackerDisadvantageOnAttackRoll(Trait):
    """Give disadvantage on attack roll to attacker."""

    def on_apply(self, target: Character) -> None:
        attr = "disadvantage.defense"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class AttackerAdvantageOnAttackRoll(Trait):
    """Give advantage on attack roll to attacker."""

    def on_apply(self, target: Character) -> None:
        attr = "advantage.defense"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class TargetDisadvantageOnAttackRoll(Trait):
    """Give disadvantage on attack roll to target."""

    def on_apply(self, target: Character) -> None:
        attr = "disadvantage.attack"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class TargetAdvantageOnAttackRoll(Trait):
    """Give advantage on attack roll to target."""

    def on_apply(self, target: Character) -> None:
        attr = "advantage.attack"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class DisadvantageOnSavingThrow(Trait):
    """Give disadvantage on saving throw to target."""

    stat: StatType

    def on_apply(self, target: Character) -> None:
        attr = f"save_disadvantage.{self.stat.name.lower()}"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class AdvantageOnSavingThrow(Trait):
    """Give advantage on saving throw to target."""

    stat: StatType

    def on_apply(self, target: Character) -> None:
        attr = f"save_advantage.{self.stat.name.lower()}"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class FailOnSavingThrow(Trait):
    """Give automatic fail on saving throw to target."""

    stat: StatType

    def on_apply(self, target: Character) -> None:
        attr = f"save_autofail.{self.stat.name.lower()}"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class SpeedMultiplier(Trait):
    """Multiply the target movement speed by a given factor."""

    value: float = Field(ge=0)

    def on_apply(self, target: Character) -> None:
        attr = "speed"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=self.value, operation="mul"))


class SpeedBonus(Trait):
    """Add a bonus to the target movement speed."""

    value: float

    def on_apply(self, target: Character) -> None:
        attr = "speed"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=self.value, operation="add"))


class ACBonus(Trait):
    """Add a bonus to the target Armor Class (AC)."""

    value: int

    def on_apply(self, target: Character) -> None:
        attr = "ac"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=self.value, operation="add"))


class AutoCritIfMelee(Trait):
    """Give automatic critical in melee range to target."""

    def is_auto_crit(self, actor: Character, target: Character) -> bool:
        return actor.distance(target.pos) <= MELEE_RANGE


class CriticalRollBonus(Trait):
    """Add a bonus to the target critical roll (e.g. value=1 -> target can roll 19 for a critical instead of 20."""

    value: int

    def on_apply(self, target: Character) -> None:
        attr = "crit_roll_bonus"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=-self.value, operation="add"))


class DamageOverTime(Trait):
    """The target receives extra damage of the given type every turn."""

    value: int
    damage_type: DamageType
    _priority = Priority.HIGH

    def on_turn_end(self, target: Character) -> None:
        damage = Damage(components=[DamageComponent(value=self.value, type=self.damage_type)])
        damage = target.modify_incoming_damage(damage)
        target.apply_damage(damage=damage.total)


class CannotMove(Trait):
    """Target cannot move."""

    def on_turn_start(self, target: Character) -> None:
        target.action_economy.movement_available = False


class CannotAct(Trait):
    """Target cannot take actions (include standard, bonus and reaction)."""

    def on_turn_start(self, target: Character) -> None:
        target.action_economy.can_act = False


class ExtraActions(Trait):
    """Give extra actions to the target."""

    extensions: list[ActionExtension]

    def on_turn_start(self, target: Character) -> None:
        target.action_economy.action_extensions.extend(self.extensions)


class HalfAttacks(Trait):
    """Halve the number of attack-type actions granted by effects."""

    _priority: int = Priority.LOW

    def on_turn_start(self, target: Character) -> None:
        economy = target.action_economy

        # Collect all extensions that add extra standard actions
        attack_extensions = [
            ext
            for ext in economy.action_extensions
            if ext.category == ActionCategory.STANDARD
            and ext.allowed_actions
            and ActionType.ATTACK in ext.allowed_actions
        ]

        # If there are multiple attack extensions we keep half of them active rounded up
        keep_count = math.ceil(len(attack_extensions) / 2)

        # Limit the number of usable attack-type extensions
        to_remove = attack_extensions[keep_count:]
        for ext in to_remove:
            economy.action_extensions.remove(ext)


class ReflectMeleeDamage(Trait):
    """Reflect a portion of the received damage of the given type to the attacker."""

    ratio: float = Field(default=0.1, ge=0, le=1)
    damage_type: DamageType
    _priority = Priority.LOW  # Execute last

    def on_receive_damage(self, actor: Character, target: Character, context: CombatContext) -> None:
        if context.damage and actor.distance(target.pos) <= MELEE_RANGE:
            value = context.damage.total * self.ratio
            damage = Damage(components=[DamageComponent(value=value, type=self.damage_type)])
            damage = actor.modify_incoming_damage(damage)
            actor.apply_damage(damage=damage.total)


class LifeSteal(Trait):
    """Heal target by a portion of the damage inflicted."""

    ratio: float = Field(default=0.1, ge=0, le=1)
    _priority = Priority.LOW  # Execute last

    def on_apply_damage(self, actor: Character, _: Character, context: CombatContext) -> None:
        if context.damage is not None:
            heal = math.ceil(context.damage.total * self.ratio)
            actor.heal(heal)


class DamageBonus(Trait):
    """Add a bonus damage component of a given type."""

    value: int
    damage_type: DamageType

    def on_apply_damage(self, actor: Character, target: Character, context: CombatContext) -> None:  # noqa: ARG002
        if context.damage is not None:
            context.damage.components.append(DamageComponent(value=self.value, type=self.damage_type, operation="add"))


class DamageMultiplier(Trait):
    """Multiply the damage component of a given type by a given factor."""

    value: int = Field(ge=0)
    damage_type: DamageType

    def on_apply_damage(self, actor: Character, target: Character, context: CombatContext) -> None:  # noqa: ARG002
        if context.damage is not None:
            context.damage.components.append(DamageComponent(value=self.value, type=self.damage_type, operation="mul"))


class IgnoreResistance(Trait):
    """Ignore target resistance to a given damage type."""

    damage_type: DamageType

    def on_apply_damage(self, _: Character, target: Character, context: CombatContext) -> None:
        res = target.attributes.damage_resistance(self.damage_type)
        if res and res.value > 0 and context.damage is not None:
            # Balance the resistance by adding the opposite vulnerability component
            context.damage.vulnerabilities.append(DamageVulnerability(value=res.value, type=self.damage_type))


class Resistance(Trait):
    """Give resistance to a given damage type to target."""

    value: float
    damage_type: DamageType

    def on_apply(self, target: Character) -> None:
        attr = f"resistance.{self.damage_type.value}"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=self.value, operation="add"))


class Immunity(Trait):
    """Give immunity to a given damage type to target."""

    damage_type: DamageType

    def on_apply(self, target: Character) -> None:
        attr = f"resistance.{self.damage_type.value}"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=1.0, operation="add"))


class Vulnerability(Trait):
    """Give vulnerability to a given damage type to target."""

    value: float
    damage_type: DamageType

    def on_apply(self, target: Character) -> None:
        attr = f"vulnerability.{self.damage_type.value}"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=self.value, operation="add"))


class SpellResistance(Trait):
    """Give spell save advantage to target."""

    def on_apply(self, target: Character) -> None:
        attr = "save_advantage.spell"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class SpellWeakness(Trait):
    """Give spell save disadvantage to target."""

    def on_apply(self, target: Character) -> None:
        attr = "save_disadvantage.spell"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class StealthDisadvantage(Trait):
    """Give stealth check disadvantage to target."""

    # TODO: Implement check
    def on_apply(self, target: Character) -> None:
        attr = "disadvantage.stealth"
        target.add_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class Regeneration(Trait):
    """Heal target by the given amount every turn."""

    value: int

    def on_turn_start(self, target: Character) -> None:
        target.heal(self.value)
