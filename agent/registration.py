from pathlib import Path

from agent.actions.common.attack import BonusAttackAction
from agent.actions.common.evocation import RepositionEvocationAction
from agent.actions.jobs.barbarian import RageAction
from agent.actions.jobs.cleric import DivineRestorationAction, PreserveLifeAction, WarPriestAction
from agent.actions.jobs.wizard import ArcaneRecoveryAction
from agent.actions.registry import ActionRegistry
from agent.models.enums import FeatureId


def register_actions() -> None:
    """Register all actions - both composable (JSON) and legacy (Python classes)."""

    # Register composable actions by JSON path (loaded on demand)
    definitions_dir = Path(__file__).parent / "actions" / "definitions"
    composable_actions = {
        # Spells
        FeatureId.MAGIC_MISSILE: "magic_missile.json",
        FeatureId.SACRED_FLAME: "sacred_flame.json",
        FeatureId.CURE_WOUNDS: "cure_wounds.json",
        FeatureId.BLESS: "bless.json",
        FeatureId.LESSER_RESTORATION: "lesser_restoration.json",
        FeatureId.DIVINE_FAVOR: "divine_favor.json",
        FeatureId.SHIELD_OF_FAITH: "shield_of_faith.json",
        FeatureId.MAGIC_WEAPON: "magic_weapon.json",
        # Class features
        FeatureId.SECOND_WIND: "second_wind.json",
    }

    for feature_id, json_file in composable_actions.items():
        json_path = str(definitions_dir / json_file)
        ActionRegistry.register(feature_id, json_path)

    # Legacy actions that still use Python classes
    # TODO: Convert these to composable format when features are available
    ActionRegistry.register(FeatureId.MELEE_SPELL_ATTACK, BonusAttackAction)
    ActionRegistry.register(FeatureId.REPOSITION_EVOCATION, RepositionEvocationAction)
    ActionRegistry.register(FeatureId.ARCANE_RECOVERY, ArcaneRecoveryAction)
    ActionRegistry.register(FeatureId.RAGE, RageAction)
    ActionRegistry.register(FeatureId.DIVINE_RESTORATION, DivineRestorationAction)
    ActionRegistry.register(FeatureId.PRESERVE_LIFE, PreserveLifeAction)
    ActionRegistry.register(FeatureId.WAR_PRIEST, WarPriestAction)
