"""Tests for RollService."""

import pytest

from agent.character.abilities import AbilityType, SkillType
from agent.character.attributes import Attributes
from agent.character.character import Character, Party
from agent.equipment.armor import Armor, ArmorType
from agent.equipment.weapons import WeaponType
from agent.jobs.fighter import Fighter
from agent.models.position import Position
from agent.services.roll_service import RollService
from tests.conftest import cheater_dice


@pytest.fixture
def test_character() -> Character:
    """Create a minimal character for testing."""
    party = Party(id="test", name="Test Party", is_player_party=True)
    return Character(
        id="test_char",
        name="Test Character",
        icon="⚔️",
        job=Fighter,
        level=5,
        pos=Position(x=0, y=0),
        attributes=Attributes(
            strength=16,
            dexterity=14,
            constitution=15,
            intelligence=10,
            wisdom=12,
            charisma=8,
            primary_ability=AbilityType.STR,
        ),
        party=party,
    )


@pytest.fixture
def target_character() -> Character:
    """Create a target character for testing."""
    party = Party(id="enemy", name="Enemies", is_player_party=False)
    return Character(
        id="target",
        name="Target",
        icon="👹",
        job=Fighter,
        level=3,
        pos=Position(x=5, y=0),
        attributes=Attributes(
            strength=14,
            dexterity=12,
            constitution=14,
            intelligence=8,
            wisdom=10,
            charisma=10,
            primary_ability=AbilityType.STR,
        ),
        party=party,
    )


def test_initiative_roll(test_character: Character) -> None:
    """Test initiative roll includes DEX modifier."""
    test_character.cheater_dice = cheater_dice(value=10)
    roll = RollService.initiative_roll(test_character)

    assert roll is not None
    assert "1d20" in roll.expression
    # DEX modifier for 14 is +2, dice rolls 10, total = 12
    assert roll.total == 12


def test_attack_roll_basic(test_character: Character, target_character: Character) -> None:
    """Test basic attack roll with STR modifier and proficiency."""
    test_character.cheater_dice = cheater_dice(value=10)
    roll = RollService.attack_roll(test_character, AbilityType.STR, WeaponType.MARTIAL_MELEE, target_character)

    assert roll is not None
    assert "1d20" in roll.expression
    # STR modifier (16) = +3, proficiency (level 5) = +3, dice = 10, total = 16
    assert roll.total == 16


def test_attack_roll_without_proficiency(test_character: Character, target_character: Character) -> None:
    """Test attack roll with weapon proficiency - Fighter is proficient with most weapons."""
    test_character.cheater_dice = cheater_dice(value=10)
    roll = RollService.attack_roll(test_character, AbilityType.STR, WeaponType.SIMPLE_MELEE, target_character)

    assert roll is not None
    # Fighter IS proficient with simple melee, so: dice (10) + STR (+3) + proficiency (+3) = 16
    assert roll.total == 16


def test_damage_roll_basic(test_character: Character) -> None:
    """Test basic damage roll."""
    test_character.cheater_dice = cheater_dice(value=5)
    roll = RollService.damage_roll(test_character, damage_dice="1d8", ability=AbilityType.STR, is_critical=False)

    assert roll is not None
    # Dice = 5, STR mod (+3) = 8
    assert roll.total == 8


def test_damage_roll_critical(test_character: Character) -> None:
    """Test critical damage roll (doubles dice)."""
    test_character.cheater_dice = cheater_dice(value=5)
    roll = RollService.damage_roll(test_character, damage_dice="1d8", ability=AbilityType.STR, is_critical=True)

    assert roll is not None
    # Critical: dice = 10 (5*2), STR mod (+3) = 13
    assert roll.total == 13


def test_damage_roll_with_base_modifier(test_character: Character) -> None:
    """Test damage roll with existing modifier in dice expression."""
    test_character.cheater_dice = cheater_dice(value=5)
    roll = RollService.damage_roll(test_character, damage_dice="1d8+2", ability=AbilityType.STR, is_critical=False)

    assert roll is not None
    # Dice = 5, base modifier (2) + ability modifier (3) = 10
    assert roll.total == 10


def test_heal_roll(test_character: Character) -> None:
    """Test healing roll with spellcasting ability."""
    test_character.attributes.spellcasting_ability = AbilityType.WIS
    test_character.cheater_dice = cheater_dice(value=8)

    roll = RollService.heal_roll(test_character, "2d8")

    assert roll is not None
    # 2d8 with each die = 8, so 8+8=16, WIS (12) modifier = +1, total = 17
    assert roll.total == 17


def test_heal_roll_without_spellcasting_ability(test_character: Character) -> None:
    """Test healing roll fails without spellcasting ability."""
    test_character.attributes.spellcasting_ability = None

    with pytest.raises(ValueError, match="cannot perform healing rolls"):
        RollService.heal_roll(test_character, "2d8")


def test_save_roll_basic(test_character: Character) -> None:
    """Test basic saving throw."""
    test_character.cheater_dice = cheater_dice(value=10)
    roll = RollService.save_roll(test_character, AbilityType.STR, is_spell=False)

    assert roll is not None
    assert "1d20" in roll.expression
    # Dice = 10, STR modifier (+3), proficiency (+3) = 16
    assert roll.total == 16


def test_save_roll_spell(test_character: Character) -> None:
    """Test spell saving throw."""
    test_character.cheater_dice = cheater_dice(value=10)
    roll = RollService.save_roll(test_character, AbilityType.DEX, is_spell=True)

    assert roll is not None
    # Dice = 10, DEX modifier (+2), no proficiency = 12 (Fighter not proficient in DEX saves)
    assert roll.total == 12


def test_save_roll_autofail(test_character: Character) -> None:
    """Test saving throw with autofail condition."""
    test_character.attributes.base_save_autofail = True

    roll = RollService.save_roll(test_character, AbilityType.STR)

    assert roll.total == 1  # Should always fail


def test_skill_check(test_character: Character) -> None:
    """Test skill check."""
    test_character.cheater_dice = cheater_dice(value=10)
    roll = RollService.skill_check(test_character, SkillType.ATHLETICS)

    assert roll is not None
    # Athletics uses STR (+3), no proficiency by default, dice = 10, total = 13
    assert roll.total == 13


def test_stealth_roll(test_character: Character) -> None:
    """Test stealth roll."""
    test_character.cheater_dice = cheater_dice(value=10)
    roll = RollService.stealth_roll(test_character)

    assert roll is not None
    # Stealth uses DEX (+2), no proficiency by default, dice = 10, total = 12
    assert roll.total == 12


def test_perception_roll(test_character: Character) -> None:
    """Test perception roll."""
    test_character.cheater_dice = cheater_dice(value=10)
    roll = RollService.perception_roll(test_character)

    assert roll is not None
    # Perception uses WIS (+1), no proficiency by default, dice = 10, total = 11
    assert roll.total == 11


def test_generic_roll() -> None:
    """Test generic dice expression roll without character."""
    roll = RollService.roll("3d6")

    assert roll is not None
    # Without character, uses real dice - just check it's in valid range
    assert 3 <= roll.total <= 18


def test_generic_roll_with_character(test_character: Character) -> None:
    """Test generic dice expression roll with character cheater dice."""
    test_character.cheater_dice = cheater_dice(value=5)
    roll = RollService.roll("1d10", character=test_character)

    assert roll is not None
    assert roll.total == 5


def test_armor_disadvantage(test_character: Character, target_character: Character) -> None:
    """Test that Fighter can wear heavy armor without disadvantage."""
    # Equip heavy armor - Fighter has proficiency with all armor
    heavy_armor = Armor(name="Plate", description="Heavy armor", armor_type=ArmorType.HEAVY, base_ac=18)
    test_character.equipment.armor = heavy_armor
    test_character.cheater_dice = cheater_dice(value=10)

    # Fighter has heavy armor proficiency, so no disadvantage
    roll = RollService.attack_roll(test_character, AbilityType.STR, WeaponType.MARTIAL_MELEE, target_character)
    assert roll is not None
    # Should work normally without disadvantage
    assert roll.total == 16
