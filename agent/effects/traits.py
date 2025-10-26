from pydantic import Field

from agent.character.modifier import Modifier
from agent.character.resources import ActionExtension
from agent.character.stats import StatType
from agent.effects.base import Priority, Trait, TraitEffect
from agent.effects.trait_effects.damage import (
    auto_crit_if_melee_effect,
    damage_bonus_effect,
    damage_multiplier_effect,
    damage_over_time_effect,
    ignore_resistance_effect,
    reflect_melee_damage_effect,
)
from agent.effects.trait_effects.support import apply_modifier, life_steal_effect, regeneration_effect
from agent.effects.trait_effects.turn import (
    cannot_act_effect,
    cannot_move_effect,
    extra_actions_effect,
    half_attacks_effect,
)
from agent.models.constants import EventType
from agent.models.damage import DamageType


class AttackerDisadvantageOnAttackRoll(Trait):
    """Give disadvantage on attack roll to attacker."""

    def get_effect(self) -> TraitEffect:
        return self._make_modifier(attr="disadvantage.defense", value=True, op="set")


class AttackerAdvantageOnAttackRoll(Trait):
    """Give advantage on attack roll to attacker."""

    def get_effect(self) -> TraitEffect:
        return self._make_modifier(attr="advantage.defense", value=True, op="set")


class TargetDisadvantageOnAttackRoll(Trait):
    """Give disadvantage on attack roll to target."""

    def get_effect(self) -> TraitEffect:
        return self._make_modifier(attr="disadvantage.attack", value=True, op="set")


class TargetAdvantageOnAttackRoll(Trait):
    """Give advantage on attack roll to target."""

    def get_effect(self) -> TraitEffect:
        return self._make_modifier(attr="advantage.attack", value=True, op="set")


class DisadvantageOnSavingThrow(Trait):
    """Give disadvantage on saving throw to target."""

    stat: StatType

    def get_effect(self) -> TraitEffect:
        return self._make_modifier(attr=f"save_disadvantage.{self.stat.name.lower()}", value=True, op="set")


class AdvantageOnSavingThrow(Trait):
    """Give advantage on saving throw to target."""

    stat: StatType

    def get_effect(self) -> TraitEffect:
        return self._make_modifier(attr=f"save_advantage.{self.stat.name.lower()}", value=True, op="set")


class FailOnSavingThrow(Trait):
    """Give automatic fail on saving throw to target."""

    stat: StatType

    def get_effect(self) -> TraitEffect:
        return self._make_modifier(attr=f"save_autofail.{self.stat.name.lower()}", value=True, op="set")


class SpeedMultiplier(Trait):
    """Multiply the target movement speed by a given factor."""

    value: float = Field(ge=0)

    def get_effect(self) -> TraitEffect:
        return self._make_modifier(attr="speed", value=self.value, op="mul")


class SpeedBonus(Trait):
    """Grant a bonus to the target movement speed."""

    value: float

    def get_effect(self) -> TraitEffect:
        return self._make_modifier(attr="speed", value=self.value, op="add")


class ACBonus(Trait):
    """Grant a bonus to the target Armor Class (AC)."""

    value: int

    def get_effect(self) -> TraitEffect:
        return self._make_modifier(attr="ac", value=self.value, op="add")


class ACBonusWithArmor(Trait):
    """Grant a bonus to Armor Class (AC) while wearing armor."""

    value: int = 1

    def get_effect(self) -> TraitEffect:
        mod = Modifier(source_id=self.id, attribute="ac", value=self.value, operation="add")
        return TraitEffect(
            source_id=self.source_id,
            dependencies=["armor"],
            event_type=EventType.MODIFIER,
            callback=lambda target: apply_modifier(target, mod, condition=bool(target.armor)),
        )


class ACBonusWithoutArmor(Trait):
    """Grant a bonus to Armor Class (AC) while not wearing armor."""

    value: int = 3

    def get_effect(self) -> TraitEffect:
        mod = Modifier(source_id=self.id, attribute="ac", value=self.value, operation="add")
        return TraitEffect(
            source_id=self.source_id,
            dependencies=["armor"],
            event_type=EventType.MODIFIER,
            callback=lambda target: apply_modifier(target, mod, condition=not bool(target.armor)),
        )


class CriticalRollBonus(Trait):
    """Add a bonus to the target critical roll (e.g. 1 -> crit on 19 instead of 20)."""

    value: int

    def get_effect(self) -> TraitEffect:
        return self._make_modifier(attr="crit_roll_bonus", value=self.value, op="add")


class Resistance(Trait):
    """Give resistance to a given damage type."""

    value: float = Field(ge=0, le=1)
    damage_type: DamageType

    def get_effect(self) -> TraitEffect:
        return self._make_modifier(attr=f"resistance.{self.damage_type.value}", value=self.value, op="add")


class Immunity(Trait):
    """Give immunity (100% resistance) to a given damage type."""

    damage_type: DamageType

    def get_effect(self) -> TraitEffect:
        return self._make_modifier(attr=f"resistance.{self.damage_type.value}", value=1.0, op="add")


class Vulnerability(Trait):
    """Give vulnerability to a given damage type."""

    value: float = Field(ge=0, le=1)
    damage_type: DamageType

    def get_effect(self) -> TraitEffect:
        return self._make_modifier(attr=f"vulnerability.{self.damage_type.value}", value=self.value, op="add")


class SpellResistance(Trait):
    """Give spell save advantage."""

    def get_effect(self) -> TraitEffect:
        return self._make_modifier(attr="save_advantage.spell", value=True, op="set")


class SpellWeakness(Trait):
    """Give spell save disadvantage."""

    def get_effect(self) -> TraitEffect:
        return self._make_modifier(attr="save_disadvantage.spell", value=True, op="set")


class StealthAdvantage(Trait):
    """Give stealth check advantage."""

    def get_effect(self) -> TraitEffect:
        return self._make_modifier(attr="advantage.stealth", value=True, op="set")


class StealthDisadvantage(Trait):
    """Give stealth check disadvantage."""

    def get_effect(self) -> TraitEffect:
        return self._make_modifier(attr="disadvantage.stealth", value=True, op="set")


class AutoCritIfMelee(Trait):
    """Give automatic critical hits when in melee range."""

    def get_effect(self) -> TraitEffect:
        return self._make_event_effect(event_type=EventType.COMBAT_START, callback=auto_crit_if_melee_effect)


class DamageOverTime(Trait):
    """Deal damage each turn."""

    value: int
    damage_type: DamageType
    _priority = Priority.HIGH

    def get_effect(self) -> TraitEffect:
        return self._make_event_effect(
            event_type=EventType.TURN_END,
            callback=lambda t: damage_over_time_effect(t, self.value, self.damage_type),
        )


class CannotMove(Trait):
    """The target cannot move during its turn."""

    def get_effect(self) -> TraitEffect:
        return self._make_event_effect(event_type=EventType.TURN_START, callback=cannot_move_effect)


class CannotAct(Trait):
    """The target cannot take any actions during its turn."""

    def get_effect(self) -> TraitEffect:
        return self._make_event_effect(event_type=EventType.TURN_START, callback=cannot_act_effect)


class ExtraActions(Trait):
    """Grant additional actions to the target at the start of its turn."""

    extensions: list[ActionExtension]

    def get_effect(self) -> TraitEffect:
        return self._make_event_effect(
            event_type=EventType.TURN_START,
            callback=lambda t: extra_actions_effect(t, self.extensions),
        )


class HalfAttacks(Trait):
    """Reduce number of attack-type extra actions by half."""

    _priority = Priority.LOW

    def get_effect(self) -> TraitEffect:
        return self._make_event_effect(event_type=EventType.TURN_START, callback=half_attacks_effect)


class ReflectMeleeDamage(Trait):
    """Reflect a portion of melee damage received back to the attacker."""

    ratio: float = Field(default=0.1, ge=0, le=1)
    damage_type: DamageType
    _priority = Priority.LOW

    def get_effect(self) -> TraitEffect:
        return self._make_event_effect(
            event_type=EventType.RECEIVE_DAMAGE,
            callback=lambda a, t, ctx: reflect_melee_damage_effect(a, t, ctx, self.ratio, self.damage_type),
        )


class LifeSteal(Trait):
    """Heal the attacker by a portion of the damage they deal."""

    ratio: float = Field(default=0.1, ge=0, le=1)
    _priority = Priority.LOW

    def get_effect(self) -> TraitEffect:
        return self._make_event_effect(
            event_type=EventType.APPLY_DAMAGE,
            callback=lambda actor, ctx: life_steal_effect(actor, ctx, self.ratio),
        )


class DamageBonus(Trait):
    """Add bonus damage of a given type to all damage dealt."""

    value: int
    damage_type: DamageType

    def get_effect(self) -> TraitEffect:
        return self._make_event_effect(
            event_type=EventType.APPLY_DAMAGE,
            callback=lambda t, ctx: damage_bonus_effect(t, ctx, self.value, self.damage_type),
        )


class DamageMultiplier(Trait):
    """Multiply damage of a specific type by a given factor."""

    value: float = Field(ge=0)
    damage_type: DamageType

    def get_effect(self) -> TraitEffect:
        return self._make_event_effect(
            event_type=EventType.APPLY_DAMAGE,
            callback=lambda t, ctx: damage_multiplier_effect(t, ctx, self.value, self.damage_type),
        )


class IgnoreResistance(Trait):
    """Negate the target's resistance to a specific damage type."""

    damage_type: DamageType

    def get_effect(self) -> TraitEffect:
        return self._make_event_effect(
            event_type=EventType.APPLY_DAMAGE,
            callback=lambda a, t, ctx: ignore_resistance_effect(a, t, ctx, self.damage_type),
        )


class Regeneration(Trait):
    """Heal target by the given amount every turn."""

    value: int

    def get_effect(self) -> TraitEffect:
        return self._make_event_effect(
            event_type=EventType.TURN_START,
            callback=lambda t: regeneration_effect(t, self.value),
        )
