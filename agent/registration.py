from agent.actions.common.spell import AttackSpellAction
from agent.actions.jobs.fighter import SecondWindAction
from agent.actions.jobs.mage import ArcaneRecoveryAction
from agent.actions.registry import ActionRegistry
from agent.effects import traits
from agent.effects.registry import TraitRegistry
from agent.jobs.features import FeatureId


def register_actions() -> None:
    ActionRegistry.register(FeatureId.SECOND_WIND, SecondWindAction)
    ActionRegistry.register(FeatureId.MAGIC_MISSILE, AttackSpellAction)
    ActionRegistry.register(FeatureId.ARCANE_RECOVERY, ArcaneRecoveryAction)


def register_traits() -> None:
    # Advantage / Disadvantage modifiers
    TraitRegistry.register(FeatureId.ATTACKER_DISADVANTAGE, traits.AttackerDisadvantageOnAttackRoll)
    TraitRegistry.register(FeatureId.ATTACKER_ADVANTAGE, traits.AttackerAdvantageOnAttackRoll)
    TraitRegistry.register(FeatureId.TARGET_DISADVANTAGE, traits.TargetDisadvantageOnAttackRoll)
    TraitRegistry.register(FeatureId.TARGET_ADVANTAGE, traits.TargetAdvantageOnAttackRoll)
    TraitRegistry.register(FeatureId.SAVE_DISADVANTAGE, traits.DisadvantageOnSavingThrow)
    TraitRegistry.register(FeatureId.SAVE_ADVANTAGE, traits.AdvantageOnSavingThrow)
    TraitRegistry.register(FeatureId.SAVE_FAIL, traits.FailOnSavingThrow)
    TraitRegistry.register(FeatureId.SPELL_SAVE_ADVANTAGE, traits.SpellResistance)
    TraitRegistry.register(FeatureId.SPELL_SAVE_DISADVANTAGE, traits.SpellWeakness)

    # Movement modifiers
    TraitRegistry.register(FeatureId.SPEED_MULTIPLIER, traits.SpeedMultiplier)
    TraitRegistry.register(FeatureId.SPEED_BONUS, traits.SpeedBonus)
    TraitRegistry.register(FeatureId.CANNOT_MOVE, traits.CannotMove)

    # Armor / AC
    TraitRegistry.register(FeatureId.AC_BONUS, traits.ACBonus)
    TraitRegistry.register(FeatureId.AC_BONUS_WITH_ARMOR, traits.ACBonusWithArmor)
    TraitRegistry.register(FeatureId.AC_BONUS_WITHOUT_ARMOR, traits.ACBonusWithoutArmor)

    # Combat and attack behavior
    TraitRegistry.register(FeatureId.CRITICAL_ROLL_BONUS, traits.CriticalRollBonus)
    TraitRegistry.register(FeatureId.AUTO_CRIT_IF_MELEE, traits.AutoCritIfMelee)
    TraitRegistry.register(FeatureId.HALF_ATTACKS, traits.HalfAttacks)
    TraitRegistry.register(FeatureId.EXTRA_ACTIONS, traits.ExtraActions)
    TraitRegistry.register(FeatureId.CANNOT_ACT, traits.CannotAct)

    # Damage modifications
    TraitRegistry.register(FeatureId.DAMAGE_BONUS, traits.DamageBonus)
    TraitRegistry.register(FeatureId.DAMAGE_MULTIPLIER, traits.DamageMultiplier)
    TraitRegistry.register(FeatureId.DAMAGE_OVER_TIME, traits.DamageOverTime)

    # Resistances and vulnerabilities
    TraitRegistry.register(FeatureId.RESISTANCE, traits.Resistance)
    TraitRegistry.register(FeatureId.IMMUNITY, traits.Immunity)
    TraitRegistry.register(FeatureId.VULNERABILITY, traits.Vulnerability)
    TraitRegistry.register(FeatureId.IGNORE_RESISTANCE, traits.IgnoreResistance)

    # Stealth and perception
    TraitRegistry.register(FeatureId.STEALTH_DISADVANTAGE, traits.StealthDisadvantage)

    # Regeneration and life steal
    TraitRegistry.register(FeatureId.REGENERATION, traits.Regeneration)
    TraitRegistry.register(FeatureId.LIFE_STEAL, traits.LifeSteal)

    # Reflection and retaliation
    TraitRegistry.register(FeatureId.REFLECT_MELEE_DAMAGE, traits.ReflectMeleeDamage)
