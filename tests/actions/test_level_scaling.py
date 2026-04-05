"""Test level-based scaling in composable actions."""

from agent.actions.registry import ActionRegistry
from agent.character.abilities import AbilityType
from agent.character.attributes import Attributes
from agent.character.character import Character, Party
from agent.character.combat_stats import CombatStats
from agent.jobs.fighter import Fighter
from agent.models.context import CombatContext
from agent.models.enums import FeatureId
from agent.models.position import Position
from agent.registration import register_actions


def test_second_wind_level_scaling(fighter: Character) -> None:
    """Test that Second Wind heals 1d10 + level."""
    register_actions()

    # Damage the fighter first
    fighter.attributes.hp = 20
    original_hp = fighter.attributes.hp

    # Use Second Wind
    action = ActionRegistry.create(FeatureId.SECOND_WIND)
    ctx = CombatContext()
    action.execute(fighter, fighter, ctx)

    # Verify healing includes level bonus
    assert ctx.heal_roll is not None
    heal_amount = ctx.heal_roll.total
    expected_min = 1 + fighter.level  # Minimum roll: 1d10=1 + level
    expected_max = 10 + fighter.level  # Maximum roll: 1d10=10 + level

    assert expected_min <= heal_amount <= expected_max
    assert fighter.attributes.hp == min(original_hp + heal_amount, fighter.max_hp)


def test_second_wind_different_levels() -> None:
    """Test that Second Wind scales correctly at different fighter levels."""
    register_actions()

    for level in [1, 5, 10, 15, 20]:
        party = Party(id="p1", name="Heroes", is_player_party=True)
        fighter = Character(
            id=f"fighter{level}",
            name=f"Fighter{level}",
            icon="⚔️",
            job=Fighter,
            level=level,
            combat=CombatStats(pos=Position(x=0, y=0)),
            attributes=Attributes(
                strength=16,
                dexterity=14,
                constitution=15,
                intelligence=10,
                wisdom=12,
                charisma=8,
                primary_ability=AbilityType.STR,
            ),
            is_player=True,
            party=party,
        )
        fighter.attributes.hp = 100
        fighter.attributes.base_hp = 100
        fighter.attributes.base_speed = 6

        # Damage the fighter
        fighter.attributes.hp = 20
        original_hp = fighter.attributes.hp

        # Use Second Wind
        action = ActionRegistry.create(FeatureId.SECOND_WIND)
        ctx = CombatContext()
        action.execute(fighter, fighter, ctx)

        # Verify healing includes level bonus
        assert ctx.heal_roll is not None
        heal_amount = ctx.heal_roll.total
        expected_min = 1 + level
        expected_max = 10 + level

        assert expected_min <= heal_amount <= expected_max, f"Level {level}: heal {heal_amount} not in [{expected_min}, {expected_max}]"
