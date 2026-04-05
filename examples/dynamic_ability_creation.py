"""Example: How the DM dynamically creates and registers abilities at runtime.

This demonstrates the end-goal architecture where no JSON files exist.
The DM creates ComposableAction instances on-the-fly and registers them.
"""

from agent.actions.base import ActionCategory, ActionType
from agent.actions.composable import ComposableAction
from agent.actions.effects.damage import DamageEffect
from agent.actions.effects.healing import HealingEffect
from agent.actions.registry import ActionRegistry
from agent.actions.resources.action_economy import ActionEconomyConsumer
from agent.actions.resources.spell_slots import SpellSlotConsumer
from agent.actions.strategies.attack_roll import AttackRollStrategy
from agent.actions.strategies.auto_success import AutoSuccessStrategy
from agent.character.abilities import AbilityType
from agent.character.resources import SpellLevel
from agent.equipment.weapons import WeaponType
from agent.models.damage import DamageType
from agent.models.enums import FeatureId, TargetingType


def dm_creates_custom_fire_spell() -> ComposableAction:
    """DM creates a custom fire spell for their campaign."""
    return ComposableAction(
        id="flame_strike_custom",
        name="Flame Strike",
        description="A column of divine fire roars down from the heavens",
        type=ActionType.CAST_SPELL,
        category=ActionCategory.STANDARD,
        targeting=TargetingType.SINGLE,
        range=12,
        hits=1,
        resolution=AttackRollStrategy(
            ability=AbilityType.WIS,
            weapon_type=WeaponType.MAGIC,
        ),
        effects=[
            DamageEffect(
                damage_dice="4d6",
                damage_type=DamageType.FIRE,
                ability=AbilityType.WIS,
            )
        ],
        resources=[
            ActionEconomyConsumer(
                category=ActionCategory.STANDARD,
                action_type=ActionType.CAST_SPELL,
            ),
            SpellSlotConsumer(level=SpellLevel.LEVEL_3),
        ],
    )


def dm_creates_healing_spell() -> ComposableAction:
    """DM creates a custom healing spell with level scaling."""
    return ComposableAction(
        id="divine_restoration_custom",
        name="Divine Restoration",
        description="Channel divine energy to heal wounds",
        type=ActionType.CAST_SPELL,
        category=ActionCategory.STANDARD,
        targeting=TargetingType.SINGLE,
        range=6,
        hits=1,
        resolution=AutoSuccessStrategy(),
        effects=[
            HealingEffect(
                heal_dice="2d8+{level}",  # Scales with caster level
                ability=AbilityType.WIS,
            )
        ],
        resources=[
            ActionEconomyConsumer(
                category=ActionCategory.STANDARD,
                action_type=ActionType.CAST_SPELL,
            ),
            SpellSlotConsumer(level=SpellLevel.LEVEL_2),
        ],
    )


def example_runtime_registration():
    """Example: How abilities are registered at runtime."""

    # DM creates a custom ability
    flame_strike = dm_creates_custom_fire_spell()

    # Register it directly (no JSON file needed!)
    # Note: In production, we'd need a dynamic ID system (string IDs or extending FeatureId)
    # For now, use FIRE_BOLT as placeholder
    ActionRegistry.register(FeatureId.FIRE_BOLT, flame_strike)

    # Now any character can use it
    action = ActionRegistry.create(FeatureId.FIRE_BOLT)
    print(f"Created action: {action.name}")
    print(f"Type: {action.__class__.__name__}")  # ComposableAction

    # DM creates another ability
    healing = dm_creates_healing_spell()

    # Register and use immediately
    ActionRegistry.register(FeatureId.PRESERVE_LIFE, healing)
    heal_action = ActionRegistry.create(FeatureId.PRESERVE_LIFE)
    print(f"\nCreated action: {heal_action.name}")


def example_ai_generated_ability() -> ComposableAction:
    """Example: AI generates ability definition from natural language.

    Future: The DM says "Create a lightning bolt that deals 3d6 damage"
    The AI generates the ComposableAction instance below.
    """

    # AI generates this from DM's description
    lightning_bolt = ComposableAction(
        id="lightning_bolt_custom",
        name="Lightning Bolt",
        description="A bolt of lightning arcs toward a target",
        type=ActionType.CAST_SPELL,
        category=ActionCategory.STANDARD,
        targeting=TargetingType.SINGLE,
        range=20,
        hits=1,
        resolution=AttackRollStrategy(
            ability=AbilityType.INT,
            weapon_type=WeaponType.MAGIC,
        ),
        effects=[
            DamageEffect(
                damage_dice="3d6",
                damage_type=DamageType.LIGHTNING,
                ability=AbilityType.INT,
            )
        ],
        resources=[
            ActionEconomyConsumer(
                category=ActionCategory.STANDARD,
                action_type=ActionType.CAST_SPELL,
            ),
            SpellSlotConsumer(level=SpellLevel.LEVEL_2),
        ],
    )

    # Register and use
    # Note: In future, the AI would generate a unique FeatureId or use a dynamic ID
    return lightning_bolt


if __name__ == "__main__":
    print("=== Dynamic Ability Creation Demo ===\n")

    print("NOTE: This is a conceptual example showing how the DM will create abilities.")
    print("In production, we'll need:")
    print("  - String-based action IDs (not just FeatureId enum)")
    print("  - AI to generate ComposableAction from natural language")
    print("  - DM interface to create/test/grant abilities\n")

    print("1. DM Creates Abilities Manually:")
    print(f"   - {dm_creates_custom_fire_spell().name}")
    print(f"   - {dm_creates_healing_spell().name}")

    print("\n2. AI Generates Abilities:")
    lightning = example_ai_generated_ability()

    print("\n✅ All abilities are pure data (ComposableAction instances)!")
    print("✅ No JSON files needed at runtime!")
    print("✅ DM can create abilities on-the-fly!")
