from enum import Enum
from typing import Literal

PartyType = Literal["players", "enemies", "neutrals"]


class Advantage(int, Enum):
    ADVANTAGE = 1
    NEUTRAL = 0
    DISADVANTAGE = -1


class TargetingType(str, Enum):
    SINGLE = "single"
    AREA = "area"
    SELF = "self"
    MULTI = "multi"
    ALLIES = "allies"


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
    AC_BONUS_MOD_WITHOUT_ARMOR = "ac_bonus_mod_without_armor"
    AC_BONUS_WITH_ARMOR_TYPES = "ac_bonus_with_armor_type"

    # Combat Behavior
    CRITICAL_ROLL_BONUS = "critical_roll_bonus"
    AUTO_CRIT_IF_MELEE = "auto_crit_if_melee"
    HALF_ATTACKS = "half_attacks"
    EXTRA_ACTIONS = "extra_actions"
    CANNOT_ACT = "cannot_act"
    ATTACK_ROLL_BONUS = "attack_roll_bonus"
    SAVE_ROLL_BONUS = "save_roll_bonus"
    EXPERTISE = "expertise"

    # Damage Modifiers
    DAMAGE_BONUS = "damage_bonus"
    DAMAGE_MULTIPLIER = "damage_multiplier"
    DAMAGE_OVER_TIME = "damage_over_time"
    DAMAGE_BONUS_WITH_ADVANTAGE = "damage_bonus_with_advantage"
    DAMAGE_BONUS_WITH_MELEE_WEAPON = "damage_bonus_with_melee_weapon"

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
    DIVINE_RESTORATION = "divine_restoration"

    # Reflection & Retaliation
    REFLECT_MELEE_DAMAGE = "reflect_melee_damage"
    SECOND_WIND = "second_wind"
    RAGE = "rage"

    # Spells
    MAGIC_MISSILE = "magic_missile"
    HASTE = "haste"
    SACRED_FLAME = "sacred_flame"
    BLESS = "bless"
    CURE_WOUNDS = "cure_wounds"


class EventType(str, Enum):
    MODIFIER = "modifier"  # Execute immediately
    TURN_START = "turn_start"
    TURN_END = "turn_end"
    COMBAT_START = "combat_start"
    COMBAT_END = "combat_end"
    APPLY_DAMAGE = "apply_damage"
    RECEIVE_DAMAGE = "receive_damage"
    ATTACK_ROLL = "attack_roll"
    SAVE_THROW = "save_throw"
