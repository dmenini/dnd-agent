"""Integration tests for composable actions in combat."""

import pytest
from pathlib import Path

from agent.actions.loader import ActionLoader
from agent.models.context import CombatContext
from agent.models.position import Position
from agent.character.character import Character


def test_longsword_attack_execution(fighter: Character, wizard: Character):
    """Test executing a longsword attack with composable action."""
    # Load action from JSON
    json_path = Path(__file__).parent.parent.parent / "agent" / "actions" / "definitions" / "longsword_attack.json"
    action = ActionLoader.from_file(json_path)

    # Use provided fixtures
    attacker = fighter
    target = wizard
    attacker.combat.pos = Position(x=0, y=0)
    target.combat.pos = Position(x=1, y=0)

    # Create context
    ctx = CombatContext()

    # Execute action
    initial_hp = target.attributes.hp
    action.execute(attacker, target, ctx)

    # Verify attack was processed
    assert ctx.attack_roll is not None
    assert hasattr(ctx, "is_hit")

    # If hit, verify damage was applied
    if ctx.is_hit:
        assert target.attributes.hp < initial_hp
        assert ctx.damage is not None
        assert ctx.damage.total > 0

    # Finalize (consume resources)
    action.finalize(attacker)

    # Verify action was consumed
    assert not attacker.action_economy.can_use_standard(action.type)


def test_fire_bolt_execution(wizard: Character, fighter: Character):
    """Test executing fire bolt spell with composable action."""
    # Load action from JSON
    json_path = Path(__file__).parent.parent.parent / "agent" / "actions" / "definitions" / "fire_bolt.json"
    action = ActionLoader.from_file(json_path)

    # Use provided fixtures
    caster = wizard
    target = fighter
    caster.combat.pos = Position(x=0, y=0)
    target.combat.pos = Position(x=5, y=0)

    # Create context
    ctx = CombatContext()

    # Execute action
    initial_hp = target.attributes.hp
    action.execute(caster, target, ctx)

    # Verify attack roll happened
    assert ctx.attack_roll is not None

    # If hit, verify fire damage was applied
    if ctx.is_hit:
        assert target.attributes.hp < initial_hp
        assert ctx.damage.components[0].type.value == "fire"

    # Finalize
    action.finalize(caster)

    # Verify action was consumed
    assert not caster.action_economy.can_use_standard(action.type)


def test_cure_wounds_execution(cleric: Character, fighter: Character):
    """Test executing cure wounds with composable action."""
    # Load action from JSON
    json_path = Path(__file__).parent.parent.parent / "agent" / "actions" / "definitions" / "cure_wounds.json"
    action = ActionLoader.from_file(json_path)

    # Use provided fixtures
    healer = cleric
    target = fighter
    healer.combat.pos = Position(x=0, y=0)
    target.combat.pos = Position(x=1, y=0)

    # Damage target first
    target.attributes.hp = target.max_hp // 2

    # Create context
    ctx = CombatContext()

    # Execute healing
    initial_hp = target.attributes.hp
    action.execute(healer, target, ctx)

    # Verify healing happened
    assert target.attributes.hp > initial_hp
    assert ctx.heal_roll is not None

    # Finalize
    action.finalize(healer)

    # Verify resources consumed
    assert not healer.action_economy.can_use_standard(action.type)


def test_composable_action_availability(fighter: Character):
    """Test action availability checking."""
    json_path = Path(__file__).parent.parent.parent / "agent" / "actions" / "definitions" / "longsword_attack.json"
    action = ActionLoader.from_file(json_path)

    # Should be available initially
    assert action.is_available(fighter.action_economy)

    # Use the action
    action.finalize(fighter)

    # Should not be available after use
    assert not action.is_available(fighter.action_economy)
