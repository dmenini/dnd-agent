from enum import Enum

from pydantic import BaseModel


class FeatureType(str, Enum):
    PASSIVE = "passive"  # trait
    ACTIVE = "active"  # action
    SPELL = "spell"


class FeatureId(str, Enum):
    """Identifiers for all registered gameplay traits and features."""

    # Advantage / Disadvantage
    ATTACKER_DISADVANTAGE = "attacker_disadvantage"
    ATTACKER_ADVANTAGE = "attacker_advantage"
    TARGET_DISADVANTAGE = "target_disadvantage"
    TARGET_ADVANTAGE = "target_advantage"
    SAVE_DISADVANTAGE = "save_disadvantage"
    SAVE_ADVANTAGE = "save_advantage"
    SPELL_SAVE_ADVANTAGE = "spell_save_advantage"
    SPELL_SAVE_DISADVANTAGE = "spell_save_disadvantage"
    SAVE_FAIL = "save_fail"

    # Movement
    SPEED_MULTIPLIER = "speed_multiplier"
    SPEED_BONUS = "speed_bonus"
    CANNOT_MOVE = "cannot_move"

    # Armor / AC
    AC_BONUS = "ac_bonus"
    AC_BONUS_WITH_ARMOR = "ac_bonus_with_armor"
    AC_BONUS_WITHOUT_ARMOR = "ac_bonus_without_armor"

    # Combat Behavior
    CRITICAL_ROLL_BONUS = "critical_roll_bonus"
    AUTO_CRIT_IF_MELEE = "auto_crit_if_melee"
    HALF_ATTACKS = "half_attacks"
    EXTRA_ACTIONS = "extra_actions"
    CANNOT_ACT = "cannot_act"

    # Damage Modifiers
    DAMAGE_BONUS = "damage_bonus"
    DAMAGE_MULTIPLIER = "damage_multiplier"
    DAMAGE_OVER_TIME = "damage_over_time"

    # Resistances & Vulnerabilities
    RESISTANCE = "resistance"
    IMMUNITY = "immunity"
    VULNERABILITY = "vulnerability"
    IGNORE_RESISTANCE = "ignore_resistance"

    # Stealth & Perception
    STEALTH = "stealth"
    STEALTH_ADVANTAGE = "stealth_advantage"
    STEALTH_DISADVANTAGE = "stealth_disadvantage"

    # Regeneration & Lifesteal
    REGENERATION = "regeneration"
    LIFE_STEAL = "life_steal"
    ARCANE_RECOVERY = "arcane_recovery"

    # Reflection & Retaliation
    REFLECT_MELEE_DAMAGE = "reflect_melee_damage"
    SECOND_WIND = "second_wind"

    # Spells
    MAGIC_MISSILE = "magic_missile"
    HASTE = "haste"


class JobFeature(BaseModel):
    """Declarative definition of a class feature that becomes a trait or action."""

    ref_id: FeatureId
    name: str
    description: str
    type: FeatureType
    level_required: int = 1
    uses_per_rest: int | None = None
    kwargs: dict = {}
