from agent.actions.common.spell import AttackSpellAction, HealingSpellAction, SupportSpellAction
from agent.actions.jobs.barbarian import RageAction
from agent.actions.jobs.cleric import DivineRestorationAction
from agent.actions.jobs.fighter import SecondWindAction
from agent.actions.jobs.wizard import ArcaneRecoveryAction
from agent.actions.registry import ActionRegistry
from agent.effects.registry import TraitRegistry
from agent.effects.traits import TraitBuilder
from agent.models.enums import FeatureId


def register_actions() -> None:
    ActionRegistry.register(FeatureId.SECOND_WIND, SecondWindAction)
    ActionRegistry.register(FeatureId.MAGIC_MISSILE, AttackSpellAction)
    ActionRegistry.register(FeatureId.ARCANE_RECOVERY, ArcaneRecoveryAction)
    ActionRegistry.register(FeatureId.SACRED_FLAME, AttackSpellAction)
    ActionRegistry.register(FeatureId.RAGE, RageAction)
    ActionRegistry.register(FeatureId.DIVINE_RESTORATION, DivineRestorationAction)
    ActionRegistry.register(FeatureId.BLESS, SupportSpellAction)
    ActionRegistry.register(FeatureId.CURE_WOUNDS, HealingSpellAction)


def register_traits() -> None:
    # Advantage / Disadvantage modifiers
    TraitRegistry.register(FeatureId.ATTACKER_DISADVANTAGE, TraitBuilder.attacker_disadvantage)
    TraitRegistry.register(FeatureId.ATTACKER_ADVANTAGE, TraitBuilder.attacker_advantage)
    TraitRegistry.register(FeatureId.TARGET_DISADVANTAGE, TraitBuilder.target_disadvantage)
    TraitRegistry.register(FeatureId.TARGET_ADVANTAGE, TraitBuilder.target_advantage)
    TraitRegistry.register(FeatureId.SAVE_DISADVANTAGE, TraitBuilder.disadvantage_on_save)
    TraitRegistry.register(FeatureId.SAVE_ADVANTAGE, TraitBuilder.advantage_on_save)
    TraitRegistry.register(FeatureId.SAVE_FAIL, TraitBuilder.autofail_save)
    TraitRegistry.register(FeatureId.SPELL_SAVE_ADVANTAGE, TraitBuilder.spell_resistance)
    TraitRegistry.register(FeatureId.SPELL_SAVE_DISADVANTAGE, TraitBuilder.spell_weakness)

    # Movement modifiers
    TraitRegistry.register(FeatureId.SPEED_MULTIPLIER, TraitBuilder.speed_multiplier)
    TraitRegistry.register(FeatureId.SPEED_BONUS, TraitBuilder.speed_bonus)
    TraitRegistry.register(FeatureId.CANNOT_MOVE, TraitBuilder.cannot_move)

    # Armor / AC
    TraitRegistry.register(FeatureId.AC_BONUS, TraitBuilder.ac_bonus)
    TraitRegistry.register(FeatureId.AC_BONUS_WITH_ARMOR, TraitBuilder.ac_bonus_with_armor)
    TraitRegistry.register(FeatureId.AC_BONUS_WITHOUT_ARMOR, TraitBuilder.ac_bonus_without_armor)
    TraitRegistry.register(FeatureId.AC_BONUS_MOD_WITHOUT_ARMOR, TraitBuilder.ac_mod_bonus_without_armor)
    TraitRegistry.register(FeatureId.AC_BONUS_WITH_ARMOR_TYPES, TraitBuilder.ac_bonus_with_armor_types)

    # Combat and attack behavior
    TraitRegistry.register(FeatureId.CRITICAL_ROLL_BONUS, TraitBuilder.critical_roll_bonus)
    TraitRegistry.register(FeatureId.AUTO_CRIT_IF_MELEE, TraitBuilder.auto_crit_if_melee)
    TraitRegistry.register(FeatureId.HALF_ATTACKS, TraitBuilder.half_attacks)
    TraitRegistry.register(FeatureId.EXTRA_ACTIONS, TraitBuilder.extra_actions)
    TraitRegistry.register(FeatureId.CANNOT_ACT, TraitBuilder.cannot_act)
    TraitRegistry.register(FeatureId.ATTACK_ROLL_BONUS, TraitBuilder.bonus_on_attack_roll)
    TraitRegistry.register(FeatureId.SAVE_ROLL_BONUS, TraitBuilder.bonus_on_save_throw)
    TraitRegistry.register(FeatureId.EXPERTISE, TraitBuilder.expertise)

    # Damage modifications
    TraitRegistry.register(FeatureId.DAMAGE_BONUS, TraitBuilder.damage_bonus)
    TraitRegistry.register(FeatureId.DAMAGE_BONUS_WITH_MELEE_WEAPON, TraitBuilder.melee_damage_bonus)
    TraitRegistry.register(FeatureId.DAMAGE_BONUS_WITH_ADVANTAGE, TraitBuilder.sneak_attack)
    TraitRegistry.register(FeatureId.DAMAGE_MULTIPLIER, TraitBuilder.damage_multiplier)
    TraitRegistry.register(FeatureId.DAMAGE_OVER_TIME, TraitBuilder.damage_over_time)

    # Resistances and vulnerabilities
    TraitRegistry.register(FeatureId.RESISTANCE, TraitBuilder.resistance)
    TraitRegistry.register(FeatureId.IMMUNITY, TraitBuilder.immunity)
    TraitRegistry.register(FeatureId.VULNERABILITY, TraitBuilder.vulnerability)
    TraitRegistry.register(FeatureId.IGNORE_RESISTANCE, TraitBuilder.ignore_resistance)

    # Stealth and perception
    TraitRegistry.register(FeatureId.STEALTH_ADVANTAGE, TraitBuilder.stealth_advantage)
    TraitRegistry.register(FeatureId.STEALTH_DISADVANTAGE, TraitBuilder.stealth_disadvantage)

    # Regeneration and life steal
    TraitRegistry.register(FeatureId.REGENERATION, TraitBuilder.regeneration)
    TraitRegistry.register(FeatureId.LIFE_STEAL, TraitBuilder.life_steal)

    # Reflection and retaliation
    TraitRegistry.register(FeatureId.REFLECT_MELEE_DAMAGE, TraitBuilder.reflect_melee_damage)
