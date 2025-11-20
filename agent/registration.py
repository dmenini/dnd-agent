from agent.actions.common.attack import BonusAttackAction
from agent.actions.common.evocation import RepositionEvocationAction
from agent.actions.common.spell import AttackSpellAction, HealingSpellAction, SupportSpellAction
from agent.actions.jobs.barbarian import RageAction
from agent.actions.jobs.cleric import DivineRestorationAction, PreserveLifeAction
from agent.actions.jobs.fighter import SecondWindAction
from agent.actions.jobs.wizard import ArcaneRecoveryAction
from agent.actions.registry import ActionRegistry
from agent.models.enums import FeatureId


def register_actions() -> None:
    ActionRegistry.register(FeatureId.MELEE_SPELL_ATTACK, BonusAttackAction)
    ActionRegistry.register(FeatureId.REPOSITION_EVOCATION, RepositionEvocationAction)

    ActionRegistry.register(FeatureId.MAGIC_MISSILE, AttackSpellAction)
    ActionRegistry.register(FeatureId.SACRED_FLAME, AttackSpellAction)
    ActionRegistry.register(FeatureId.CURE_WOUNDS, HealingSpellAction)
    ActionRegistry.register(FeatureId.BLESS, SupportSpellAction)

    ActionRegistry.register(FeatureId.SECOND_WIND, SecondWindAction)
    ActionRegistry.register(FeatureId.ARCANE_RECOVERY, ArcaneRecoveryAction)
    ActionRegistry.register(FeatureId.RAGE, RageAction)
    ActionRegistry.register(FeatureId.DIVINE_RESTORATION, DivineRestorationAction)
    ActionRegistry.register(FeatureId.PRESERVE_LIFE, PreserveLifeAction)
