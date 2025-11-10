from typing import Any, Literal

from pydantic import Field

from agent.character.abilities import AbilityType
from agent.character.proficiency import ProficiencyTarget
from agent.character.resources import ActionExtension
from agent.effects.base import ModifierTrait, Priority, Trait
from agent.effects.trait_effects.damage import (
    auto_crit_if_melee_effect,
    damage_bonus_effect,
    damage_multiplier_effect,
    damage_over_time_effect,
    ignore_resistance_effect,
    reflect_melee_damage_effect,
    sneak_attack_effect,
)
from agent.effects.trait_effects.support import (
    bonus_attack_roll_effect,
    bonus_save_roll_effect,
    life_steal_effect,
    regeneration_effect,
)
from agent.effects.trait_effects.turn import (
    cannot_act_effect,
    cannot_move_effect,
    extra_actions_effect,
    half_attacks_effect,
)
from agent.equipment.armor import ArmorType
from agent.models.constants import EventType
from agent.models.damage import DamageType

# ============================================================================
# MODIFIER TRAITS - Direct attribute modifications
# ============================================================================


class AttackerDisadvantageOnAttackRoll(ModifierTrait):
    """Give disadvantage on attack roll to attacker."""

    attribute: str = "disadvantage.defense"
    value: bool = True
    operation: Literal["set", "add", "mul"] = "set"


class AttackerAdvantageOnAttackRoll(ModifierTrait):
    """Give advantage on attack roll to attacker."""

    attribute: str = "advantage.defense"
    value: bool = True
    operation: Literal["set", "add", "mul"] = "set"


class TargetDisadvantageOnAttackRoll(ModifierTrait):
    """Give disadvantage on attack roll to target."""

    attribute: str = "disadvantage.attack"
    value: bool = True
    operation: Literal["set", "add", "mul"] = "set"


class TargetAdvantageOnAttackRoll(ModifierTrait):
    """Give advantage on attack roll to target."""

    attribute: str = "advantage.attack"
    value: bool = True
    operation: Literal["set", "add", "mul"] = "set"


class DisadvantageOnSavingThrow(ModifierTrait):
    """Give disadvantage on saving throw to target."""

    attribute: str = "save_disadvantage.{ability}"
    ability: AbilityType
    value: bool = True
    operation: Literal["set", "add", "mul"] = "set"

    def model_post_init(self, _: Any) -> None:
        super().model_post_init(_)
        self.attribute = self.attribute.format(ability=self.ability.value)


class AdvantageOnSavingThrow(ModifierTrait):
    """Give advantage on saving throw to target."""

    attribute: str = "save_advantage.{ability}"
    ability: AbilityType
    value: bool = True
    operation: Literal["set", "add", "mul"] = "set"

    def model_post_init(self, _: Any) -> None:
        super().model_post_init(_)
        self.attribute = self.attribute.format(ability=self.ability.value)


class FailOnSavingThrow(ModifierTrait):
    """Give automatic fail on saving throw to target."""

    attribute: str = "save_autofail.{ability}"
    ability: AbilityType
    value: bool = True
    operation: Literal["set", "add", "mul"] = "set"

    def model_post_init(self, _: Any) -> None:
        super().model_post_init(_)
        self.attribute = self.attribute.format(ability=self.ability.value)


class SpeedMultiplier(ModifierTrait):
    """Multiply the target movement speed by a given factor."""

    attribute: str = "speed"
    value: float = Field(ge=0)
    operation: Literal["set", "add", "mul"] = "mul"


class SpeedBonus(ModifierTrait):
    """Grant a bonus to the target movement speed."""

    attribute: str = "speed"
    value: float
    operation: Literal["set", "add", "mul"] = "add"


class ACBonus(ModifierTrait):
    """Grant a bonus to the target Armor Class (AC)."""

    attribute: str = "ac"
    value: int
    operation: Literal["set", "add", "mul"] = "add"


class ACBonusWithArmor(ACBonus):
    """Grant a bonus to Armor Class (AC) while wearing armor."""

    value: int = 1

    def condition(self, target: Any) -> bool:
        return bool(target.armor)

    def condition_depends_on(self, field_name: str) -> bool:
        return field_name == "armor"


class ACBonusWithArmorTypes(ACBonus):
    """Grant a bonus to Armor Class (AC) while wearing armor of certain types."""

    value: int = 1
    armor_types: list[ArmorType]

    def condition(self, target: Any) -> bool:
        return target.armor and target.armor.armor_type in self.armor_types

    def condition_depends_on(self, field_name: str) -> bool:
        return field_name == "armor"


class ACBonusWithoutArmor(ACBonus):
    """Grant a bonus to Armor Class (AC) while not wearing armor."""

    value: int = 3

    def condition(self, target: Any) -> bool:
        return not bool(target.armor)

    def condition_depends_on(self, field_name: str) -> bool:
        return field_name == "armor"


class ACBonusModWithoutArmor(ModifierTrait):
    """Gain a bonus ability modifier to Armor Class (AC) while not wearing armor."""

    attribute: str = "ac_mod.{ability}"
    value: bool = True
    operation: Literal["set", "add", "mul"] = "set"
    ability: AbilityType = AbilityType.CON

    def model_post_init(self, _: Any) -> None:
        super().model_post_init(_)
        self.attribute = self.attribute.format(ability=self.ability.value)

    def condition(self, target: Any) -> bool:
        return not bool(target.armor)

    def condition_depends_on(self, field_name: str) -> bool:
        return field_name == "armor"


class CriticalRollBonus(ModifierTrait):
    """Add a bonus to the target critical roll (e.g. 1 -> crit on 19 instead of 20)."""

    attribute: str = "crit_roll_bonus"
    value: int
    operation: Literal["set", "add", "mul"] = "add"


class Resistance(ModifierTrait):
    """Give resistance to a given damage type."""

    attribute: str = "resistance.{damage_type}"
    value: float = Field(ge=0, le=1)
    damage_type: DamageType
    operation: Literal["set", "add", "mul"] = "add"

    def model_post_init(self, _: Any) -> None:
        super().model_post_init(_)
        self.attribute = self.attribute.format(damage_type=self.damage_type.value)


class Immunity(ModifierTrait):
    """Give immunity (100% resistance) to a given damage type."""

    attribute: str = "resistance.{damage_type}"
    damage_type: DamageType
    value: float = 1.0
    operation: Literal["set", "add", "mul"] = "add"

    def model_post_init(self, _: Any) -> None:
        super().model_post_init(_)
        self.attribute = self.attribute.format(damage_type=self.damage_type.value)


class Vulnerability(ModifierTrait):
    """Give vulnerability to a given damage type."""

    attribute: str = "vulnerability.{damage_type}"
    value: float = Field(ge=0, le=1)
    damage_type: DamageType
    operation: Literal["set", "add", "mul"] = "add"

    def model_post_init(self, _: Any) -> None:
        super().model_post_init(_)
        self.attribute = self.attribute.format(damage_type=self.damage_type.value)


class SpellResistance(ModifierTrait):
    """Give spell save advantage."""

    attribute: str = "save_advantage.spell"
    value: bool = True
    operation: Literal["set", "add", "mul"] = "set"


class SpellWeakness(ModifierTrait):
    """Give spell save disadvantage."""

    attribute: str = "save_disadvantage.spell"
    value: bool = True
    operation: Literal["set", "add", "mul"] = "set"


class StealthAdvantage(ModifierTrait):
    """Give stealth check advantage."""

    attribute: str = "advantage.stealth"
    value: bool = True
    operation: Literal["set", "add", "mul"] = "set"


class StealthDisadvantage(ModifierTrait):
    """Give stealth check disadvantage."""

    attribute: str = "disadvantage.stealth"
    value: bool = True
    operation: Literal["set", "add", "mul"] = "set"


class Expertise(ModifierTrait):
    """Give expertise with a certain skill, weapon, armor or save ability."""

    proficiency: ProficiencyTarget
    attribute: str = "disadvantage.{proficiency}"
    value: bool = True
    operation: Literal["set", "add", "mul"] = "set"

    def model_post_init(self, _: Any) -> None:
        super().model_post_init(_)
        self.attribute = self.attribute.format(proficiency=self.proficiency.value)


# ============================================================================
# EVENT TRAITS - Callback-based effects
# ============================================================================


class AutoCritIfMelee(Trait):
    """Give automatic critical hits when in melee range."""

    event_type: EventType = EventType.COMBAT_START

    def apply(self, actor: Any, target: Any, ctx: Any) -> None:
        auto_crit_if_melee_effect(actor, target, ctx)


class DamageOverTime(Trait):
    """Deal damage each turn."""

    event_type: EventType = EventType.TURN_END
    value: int
    damage_type: DamageType
    priority: int = Priority.HIGH

    def apply(self, target: Any) -> None:
        damage_over_time_effect(target, self.value, self.damage_type)


class CannotMove(Trait):
    """The target cannot move during its turn."""

    event_type: EventType = EventType.TURN_START

    def apply(self, target: Any) -> None:
        cannot_move_effect(target)


class CannotAct(Trait):
    """The target cannot take any actions during its turn."""

    event_type: EventType = EventType.TURN_START

    def apply(self, target: Any) -> None:
        cannot_act_effect(target)


class ExtraActions(Trait):
    """Grant additional actions to the target at the start of its turn."""

    event_type: EventType = EventType.TURN_START
    extensions: list[ActionExtension]

    def apply(self, target: Any) -> None:
        extra_actions_effect(target, self.extensions)


class HalfAttacks(Trait):
    """Reduce number of attack-type extra actions by half."""

    event_type: EventType = EventType.TURN_START
    priority: int = Priority.LOW

    def apply(self, target: Any) -> None:
        half_attacks_effect(target)


class BonusOnAttackRoll(Trait):
    """The target can roll a d4 and add the number rolled to the attack roll."""

    event_type: EventType = EventType.ATTACK_ROLL
    dice_expr: str = "1d4"

    def apply(self, actor: Any, target: Any, ctx: Any) -> None:  # noqa: ARG002
        bonus_attack_roll_effect(actor, ctx, expr=self.dice_expr)


class BonusOnSaveThrow(Trait):
    """The target can roll a d4 and add the number rolled to the save throw."""

    event_type: EventType = EventType.SAVE_THROW
    dice_expr: str = "1d4"

    def apply(self, actor: Any, target: Any, ctx: Any) -> None:  # noqa: ARG002
        bonus_save_roll_effect(actor, ctx, expr=self.dice_expr)


class ReflectMeleeDamage(Trait):
    """Reflect a portion of melee damage received back to the attacker."""

    event_type: EventType = EventType.RECEIVE_DAMAGE
    ratio: float = Field(default=0.1, ge=0, le=1)
    damage_type: DamageType
    priority: int = Priority.LOW

    def apply(self, actor: Any, target: Any, ctx: Any) -> None:
        reflect_melee_damage_effect(actor, target, ctx, ratio=self.ratio, damage_type=self.damage_type)


class LifeSteal(Trait):
    """Heal the attacker by a portion of the damage they deal."""

    event_type: EventType = EventType.APPLY_DAMAGE
    ratio: float = Field(default=0.1, ge=0, le=1)
    priority: int = Priority.LOW

    def apply(self, actor: Any, ctx: Any) -> None:
        life_steal_effect(actor, ctx, ratio=self.ratio)


class DamageBonus(Trait):
    """Add bonus damage of a given type to all damage dealt."""

    event_type: EventType = EventType.APPLY_DAMAGE
    value: int
    damage_type: DamageType

    def apply(self, target: Any, ctx: Any) -> None:
        damage_bonus_effect(target, ctx, value=self.value, damage_type=self.damage_type)


class DamageBonusWithAdvantage(Trait):
    """Add bonus damage roll in case of attack with advantage with finesse or ranged weapons (once per turn)."""

    event_type: EventType = EventType.APPLY_DAMAGE
    dice_expr: str

    def apply(self, target: Any, ctx: Any) -> None:
        sneak_attack_effect(target, ctx, dice=self.dice_expr)


class DamageMultiplier(Trait):
    """Multiply damage of a specific type by a given factor."""

    event_type: EventType = EventType.APPLY_DAMAGE
    value: float = Field(ge=0)
    damage_type: DamageType

    def apply(self, target: Any, ctx: Any) -> None:
        damage_multiplier_effect(target, ctx, value=self.value, damage_type=self.damage_type)


class IgnoreResistance(Trait):
    """Negate the target's resistance to a specific damage type."""

    event_type: EventType = EventType.APPLY_DAMAGE
    damage_type: DamageType

    def apply(self, actor: Any, target: Any, ctx: Any) -> None:
        ignore_resistance_effect(actor, target, ctx, damage_type=self.damage_type)


class Regeneration(Trait):
    """Heal target by the given amount every turn."""

    event_type: EventType = EventType.TURN_START
    value: int

    def apply(self, target: Any) -> None:
        regeneration_effect(target, value=self.value)
