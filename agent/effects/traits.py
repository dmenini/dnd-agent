from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from agent.character.modifier import Modifier
from agent.character.resources import ActionExtension
from agent.character.stats import StatType
from agent.effects.base import Priority, Trait
from agent.effects.trait_effects.damage import (
    auto_crit_if_melee_effect,
    damage_bonus_effect,
    damage_multiplier_effect,
    damage_over_time_effect,
    ignore_resistance_effect,
    reflect_melee_damage_effect,
)
from agent.effects.trait_effects.support import life_steal_effect, regeneration_effect
from agent.effects.trait_effects.turn import (
    cannot_act_effect,
    cannot_move_effect,
    extra_actions_effect,
    half_attacks_effect,
)
from agent.models.constants import TRAIT_LOG_LEVEL, EventType
from agent.models.damage import DamageType

if TYPE_CHECKING:
    from agent.character.resolvers.base import CharacterBase


class AttackerDisadvantageOnAttackRoll(Trait):
    """Give disadvantage on attack roll to attacker."""

    def on_apply(self, target: CharacterBase) -> None:
        attr = "disadvantage.defense"
        target.register_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class AttackerAdvantageOnAttackRoll(Trait):
    """Give advantage on attack roll to attacker."""

    def on_apply(self, target: CharacterBase) -> None:
        attr = "advantage.defense"
        target.register_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class TargetDisadvantageOnAttackRoll(Trait):
    """Give disadvantage on attack roll to target."""

    def on_apply(self, target: CharacterBase) -> None:
        attr = "disadvantage.attack"
        target.register_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class TargetAdvantageOnAttackRoll(Trait):
    """Give advantage on attack roll to target."""

    def on_apply(self, target: CharacterBase) -> None:
        attr = "advantage.attack"
        target.register_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class DisadvantageOnSavingThrow(Trait):
    """Give disadvantage on saving throw to target."""

    stat: StatType

    def on_apply(self, target: CharacterBase) -> None:
        attr = f"save_disadvantage.{self.stat.name.lower()}"
        target.register_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class AdvantageOnSavingThrow(Trait):
    """Give advantage on saving throw to target."""

    stat: StatType

    def on_apply(self, target: CharacterBase) -> None:
        attr = f"save_advantage.{self.stat.name.lower()}"
        target.register_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class FailOnSavingThrow(Trait):
    """Give automatic fail on saving throw to target."""

    stat: StatType

    def on_apply(self, target: CharacterBase) -> None:
        attr = f"save_autofail.{self.stat.name.lower()}"
        target.register_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class SpeedMultiplier(Trait):
    """Multiply the target movement speed by a given factor."""

    value: float = Field(ge=0)

    def on_apply(self, target: CharacterBase) -> None:
        attr = "speed"
        target.register_modifier(Modifier(source_id=self._id, attribute=attr, value=self.value, operation="mul"))


class SpeedBonus(Trait):
    """Grant a bonus to the target movement speed."""

    value: float

    def on_apply(self, target: CharacterBase) -> None:
        attr = "speed"
        target.register_modifier(Modifier(source_id=self._id, attribute=attr, value=self.value, operation="add"))


class ACBonus(Trait):
    """Grant a bonus to the target Armor Class (AC)."""

    value: int

    def on_apply(self, target: CharacterBase) -> None:
        attr = "ac"
        target.register_modifier(Modifier(source_id=self._id, attribute=attr, value=self.value, operation="add"))
        target.log_event(f"{target.name} gains +{self.value} AC from {self.source_id}.", event_type=TRAIT_LOG_LEVEL)


class ACBonusWithArmor(ACBonus):
    """Grant a bonus to the target Armor Class (AC) while wearing armor."""

    value: int = Field(default=1)

    def on_apply(self, target: CharacterBase) -> None:
        if target.armor:
            super().on_apply(target)


class ACBonusWithoutArmor(ACBonus):
    """Grant a bonus to the target Armor Class (AC) while wearing armor."""

    value: int = Field(default=3)

    def on_apply(self, target: CharacterBase) -> None:
        if not target.armor:
            super().on_apply(target)


class CriticalRollBonus(Trait):
    """Add a bonus to the target critical roll (e.g. value=1 -> target can roll 19 for a critical instead of 20."""

    value: int

    def on_apply(self, target: CharacterBase) -> None:
        attr = "crit_roll_bonus"
        target.register_modifier(Modifier(source_id=self._id, attribute=attr, value=-self.value, operation="add"))


class Resistance(Trait):
    """Give resistance to a given damage type to target."""

    value: float
    damage_type: DamageType

    def on_apply(self, target: CharacterBase) -> None:
        attr = f"resistance.{self.damage_type.value}"
        target.register_modifier(Modifier(source_id=self._id, attribute=attr, value=self.value, operation="add"))


class Immunity(Trait):
    """Give immunity to a given damage type to target."""

    damage_type: DamageType

    def on_apply(self, target: CharacterBase) -> None:
        attr = f"resistance.{self.damage_type.value}"
        target.register_modifier(Modifier(source_id=self._id, attribute=attr, value=1.0, operation="add"))


class Vulnerability(Trait):
    """Give vulnerability to a given damage type to target."""

    value: float
    damage_type: DamageType

    def on_apply(self, target: CharacterBase) -> None:
        attr = f"vulnerability.{self.damage_type.value}"
        target.register_modifier(Modifier(source_id=self._id, attribute=attr, value=self.value, operation="add"))


class SpellResistance(Trait):
    """Give spell save advantage to target."""

    def on_apply(self, target: CharacterBase) -> None:
        attr = "save_advantage.spell"
        target.register_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class SpellWeakness(Trait):
    """Give spell save disadvantage to target."""

    def on_apply(self, target: CharacterBase) -> None:
        attr = "save_disadvantage.spell"
        target.register_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class StealthAdvantage(Trait):
    """Give stealth check advantage to target."""

    def on_apply(self, target: CharacterBase) -> None:
        attr = "advantage.stealth"
        target.register_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class StealthDisadvantage(Trait):
    """Give stealth check disadvantage to target."""

    def on_apply(self, target: CharacterBase) -> None:
        attr = "disadvantage.stealth"
        target.register_modifier(Modifier(source_id=self._id, attribute=attr, value=True, operation="set"))


class AutoCritIfMelee(Trait):
    """Give automatic critical hits when in melee range."""

    def on_apply(self, target: CharacterBase) -> None:
        target.register_listener(EventType.COMBAT_START, callback=auto_crit_if_melee_effect, source_id=self._id)


class DamageOverTime(Trait):
    """Deal damage each turn."""

    value: int
    damage_type: DamageType
    _priority = Priority.HIGH

    def on_apply(self, target: CharacterBase) -> None:
        target.register_listener(
            EventType.TURN_END,
            callback=lambda t: damage_over_time_effect(t, self.value, self.damage_type),
            source_id=self._id,
        )


class CannotMove(Trait):
    """The target cannot move during its turn."""

    def on_apply(self, target: CharacterBase) -> None:
        target.register_listener(EventType.TURN_START, callback=cannot_move_effect, source_id=self._id)


class CannotAct(Trait):
    """The target cannot take any actions during its turn."""

    def on_apply(self, target: CharacterBase) -> None:
        target.register_listener(EventType.TURN_START, callback=cannot_act_effect, source_id=self._id)


class ExtraActions(Trait):
    """Grant additional actions to the target at the start of its turn."""

    extensions: list[ActionExtension]

    def on_apply(self, target: CharacterBase) -> None:
        target.register_listener(
            EventType.TURN_START,
            callback=lambda t: extra_actions_effect(t, self.extensions),
            source_id=self._id,
        )


class HalfAttacks(Trait):
    """Reduce the number of attack-type extra actions by half, rounded up."""

    _priority: int = Priority.LOW

    def on_apply(self, target: CharacterBase) -> None:
        target.register_listener(EventType.TURN_START, callback=half_attacks_effect, source_id=self._id)


class ReflectMeleeDamage(Trait):
    """Reflect a portion of melee damage received back to the attacker."""

    ratio: float = Field(default=0.1, ge=0, le=1)
    damage_type: DamageType
    _priority = Priority.LOW

    def on_apply(self, target: CharacterBase) -> None:
        target.register_listener(
            EventType.RECEIVE_DAMAGE,
            callback=lambda a, t, ctx: reflect_melee_damage_effect(a, t, ctx, self.ratio, self.damage_type),
            source_id=self._id,
        )


class LifeSteal(Trait):
    """Heal the attacker by a portion of the damage they deal."""

    ratio: float = Field(default=0.1, ge=0, le=1)
    _priority = Priority.LOW

    def on_apply(self, target: CharacterBase) -> None:
        target.register_listener(
            EventType.APPLY_DAMAGE,
            lambda actor, ctx: life_steal_effect(actor, ctx, self.ratio),
            source_id=self._id,
        )


class DamageBonus(Trait):
    """Add a bonus damage component of a given type to all damage dealt."""

    value: int
    damage_type: DamageType

    def on_apply(self, target: CharacterBase) -> None:
        target.register_listener(
            EventType.APPLY_DAMAGE,
            lambda t, ctx: damage_bonus_effect(t, ctx, self.value, self.damage_type),
            source_id=self._id,
        )


class DamageMultiplier(Trait):
    """Multiply damage of a specific type by the given factor."""

    value: float = Field(ge=0)
    damage_type: DamageType

    def on_apply(self, target: CharacterBase) -> None:
        target.register_listener(
            EventType.APPLY_DAMAGE,
            lambda t, ctx: damage_multiplier_effect(t, ctx, self.value, self.damage_type),
            source_id=self._id,
        )


class IgnoreResistance(Trait):
    """Negate the target's resistance to a specific damage type."""

    damage_type: DamageType

    def on_apply(self, target: CharacterBase) -> None:
        target.register_listener(
            EventType.APPLY_DAMAGE,
            lambda a, t, ctx: ignore_resistance_effect(a, t, ctx, self.damage_type),
            source_id=self._id,
        )


class Regeneration(Trait):
    """Heal target by the given amount every turn."""

    value: int

    def on_apply(self, target: CharacterBase) -> None:
        target.register_listener(
            EventType.TURN_START,
            lambda t: regeneration_effect(t, self.value),
            source_id=self._id,
        )
