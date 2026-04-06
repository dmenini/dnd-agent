"""Examples of using the DM action builder tool to create custom actions.

This tool allows the DM agent to dynamically create abilities for:
- Boss monsters with unique attacks
- Environmental hazards (traps, magical effects)
- Special items with active abilities
- Narrative-driven actions
"""

import json
import sys
from pathlib import Path

# Add parent directory to path so we can import agent
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.actions.base import ActionCategory, ActionType
from agent.actions.composable import ComposableAction
from agent.actions.effects.damage import DamageEffect
from agent.actions.effects.healing import HealingEffect
from agent.actions.resources.action_economy import ActionEconomyConsumer
from agent.actions.strategies.attack_roll import AttackRollStrategy
from agent.actions.strategies.auto_success import AutoSuccessStrategy
from agent.actions.strategies.saving_throw import SavingThrowStrategy
from agent.ai.dm.action_builder_tool import create_custom_action
from agent.character.abilities import AbilityType
from agent.equipment.weapons import WeaponType
from agent.models.damage import DamageType
from agent.models.enums import TargetingType


def example_boss_attack():
    """Create a dragon's fire breath attack."""
    print("=== Creating Dragon Fire Breath ===")

    action = ComposableAction(
        id="dragon_fire_breath",
        name="Fire Breath",
        description="The dragon exhales a cone of searing flames",
        type=ActionType.SPECIAL,
        category=ActionCategory.STANDARD,
        targeting=TargetingType.MULTI,
        range=30.0,
        hits=1,
        resolution=SavingThrowStrategy(ability=AbilityType.DEX, use_spell_dc=True),
        effects=[DamageEffect(damage_dice="10d6", damage_type=DamageType.FIRE, ability=None, half_on_save=False)],
        resources=[ActionEconomyConsumer(category=ActionCategory.STANDARD, action_type=ActionType.SPECIAL)],
        level_required=10,
        metadata={"dm_created": True},
    )

    result = create_custom_action.invoke({"action": action})
    print(result)
    print()


def example_environmental_hazard():
    """Create a falling rocks trap."""
    print("=== Creating Falling Rocks Trap ===")

    action = ComposableAction(
        id="falling_rocks",
        name="Falling Rocks",
        description="Rocks fall from the ceiling, dealing bludgeoning damage",
        type=ActionType.SPECIAL,
        category=ActionCategory.REACTION,
        targeting=TargetingType.AREA,
        range=20.0,
        hits=1,
        resolution=SavingThrowStrategy(ability=AbilityType.DEX, use_spell_dc=False),
        effects=[
            DamageEffect(damage_dice="4d10", damage_type=DamageType.BLUDGEONING, ability=None, half_on_save=True)
        ],
        resources=[ActionEconomyConsumer(category=ActionCategory.REACTION, action_type=ActionType.SPECIAL)],
        level=1,
        metadata={"dm_created": True},
    )

    result = create_custom_action.invoke({"action": action})
    print(result)
    print()


def example_special_weapon():
    """Create a legendary weapon's special attack."""
    print("=== Creating Vorpal Sword Beheading ===")

    action = ComposableAction(
        id="vorpal_behead",
        name="Vorpal Strike",
        description="Strike with legendary sharpness, potentially beheading the foe",
        type=ActionType.ATTACK,
        category=ActionCategory.STANDARD,
        targeting=TargetingType.SINGLE,
        range=1.5,
        hits=1,
        resolution=AttackRollStrategy(ability=AbilityType.STRENGTH, weapon_type=WeaponType.MARTIAL_MELEE),
        effects=[
            DamageEffect(
                damage_dice="2d8+10", damage_type=DamageType.SLASHING, ability=AbilityType.STRENGTH, half_on_save=False
            )
        ],
        resources=[ActionEconomyConsumer(category=ActionCategory.STANDARD, action_type=ActionType.ATTACK)],
        level_required=15,
        metadata={"dm_created": True},
    )

    result = create_custom_action.invoke({"action": action})
    print(result)
    print()


def example_healing_ability():
    """Create a healing ability for a cleric NPC."""
    print("=== Creating Mass Heal ===")

    action = ComposableAction(
        id="mass_heal",
        name="Mass Heal",
        description="Channel divine energy to heal multiple allies",
        type=ActionType.CAST_SPELL,
        category=ActionCategory.STANDARD,
        targeting=TargetingType.MULTI,
        range=30.0,
        hits=3,
        resolution=AutoSuccessStrategy(),
        effects=[HealingEffect(heal_dice="5d8+20", ability=None)],
        resources=[ActionEconomyConsumer(category=ActionCategory.STANDARD, action_type=ActionType.CAST_SPELL)],
        level_required=9,
        metadata={"dm_created": True},
    )

    result = create_custom_action.invoke({"action": action})
    print(result)

    # Show how to use the created action
    json_str = result.split("\n\n", 1)[1]
    action_data = json.loads(json_str)
    action = ComposableAction.model_validate(action_data)

    print("\n=== Action can be used in combat ===")
    print(f"Action ID: {action.id}")
    print(f"Type: {action.type}")
    print(f"Category: {action.category}")
    print(f"Hits: {action.hits} targets")
    print()


def example_vampiric_attack():
    """Create an attack that damages and heals."""
    print("=== Creating Vampiric Touch ===")

    action = ComposableAction(
        id="vampiric_touch",
        name="Vampiric Touch",
        description="Drain the life force from your target, healing yourself",
        type=ActionType.CAST_SPELL,
        category=ActionCategory.STANDARD,
        targeting=TargetingType.SINGLE,
        range=1.5,
        hits=1,
        resolution=AttackRollStrategy(ability=AbilityType.INT, weapon_type=WeaponType.MAGIC),
        effects=[
            DamageEffect(damage_dice="3d6", damage_type=DamageType.NECROTIC, ability=None, half_on_save=False),
            HealingEffect(heal_dice="3d6", ability=None),
        ],
        resources=[ActionEconomyConsumer(category=ActionCategory.STANDARD, action_type=ActionType.CAST_SPELL)],
        level_required=3,
        metadata={"dm_created": True},
    )

    result = create_custom_action.invoke({"action": action})
    print(result)
    print()


if __name__ == "__main__":
    print("DM Custom Action Examples")
    print("=" * 60)
    print()

    example_boss_attack()
    example_environmental_hazard()
    example_special_weapon()
    example_healing_ability()
    example_vampiric_attack()

    print("\n" + "=" * 60)
    print("These actions can be:")
    print("- Added to NPC character sheets")
    print("- Used in scripted encounters")
    print("- Registered with ActionRegistry for reuse")
    print("- Modified on-the-fly during gameplay")

