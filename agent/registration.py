from pathlib import Path

from agent.actions.registry import ActionRegistry
from agent.models.enums import FeatureId


def register_actions() -> None:
    """Register all composable actions from JSON definitions.

    Note: Some actions like character movement and evocation repositioning are
    implicit and don't need registration - they're always available by default.
    """

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
        FeatureId.SPIRITUAL_WEAPON: "spiritual_weapon.json",
        # Class features
        FeatureId.SECOND_WIND: "second_wind.json",
        FeatureId.ARCANE_RECOVERY: "arcane_recovery.json",
        FeatureId.RAGE: "rage.json",
        FeatureId.WAR_PRIEST: "war_priest.json",
        FeatureId.PRESERVE_LIFE: "preserve_life.json",
        # Evocation actions
        FeatureId.MELEE_SPELL_ATTACK: "melee_spell_attack.json",
    }

    for feature_id, json_file in composable_actions.items():
        json_path = str(definitions_dir / json_file)
        ActionRegistry.register(feature_id, json_path)
