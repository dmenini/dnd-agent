"""Tests for character creation agent tools."""

# mypy: disable-error-code="index,union-attr,operator"

from collections.abc import Callable
from typing import Any

from langchain_core.messages import ToolMessage
from langgraph.types import Command

from agent.ai.character_creation.tools import (
    finalize_character,
    finalize_party,
    get_class_options,
    get_party_status,
    save_base_character,
    save_skills,
    save_starting_equipment,
    save_subclass,
)
from agent.character.abilities import AbilityType, SkillType
from agent.character.builder import CharacterBuilder, CharacterSelections
from agent.equipment.armor import Armor, ArmorType
from agent.equipment.base import EquipmentSlot
from agent.equipment.weapons import MeleeWeapon, WeaponHandling, WeaponType
from agent.jobs.base import JobType
from agent.models.damage import DamageType


def test_get_class_options_with_subclass() -> None:
    """Test get_class_options for Cleric returns subclass options."""
    result = get_class_options.invoke({"job_type": JobType.CLERIC})

    assert "cleric" in result.lower()
    assert "Options for player choice" in result
    # Cleric has 7 domains
    assert "life_domain" in result


def test_get_class_options_no_subclass() -> None:
    """Test get_class_options for Fighter returns no subclass options."""
    result = get_class_options.invoke({"job_type": JobType.FIGHTER})

    assert "fighter" in result.lower()
    assert "No choices available" in result


def test_save_base_character_new(mock_tool_runtime: Callable[[dict], Any]) -> None:
    """Test saving a new base character."""
    runtime = mock_tool_runtime(
        {
            "current_builder": None,
            "party": [],
            "max_players": 2,
        }
    )

    character = CharacterBuilder(
        name="Test Hero",
        icon="⚔️",
        job=JobType.FIGHTER,
    )

    result = save_base_character.invoke({"character": character, "runtime": runtime})

    assert isinstance(result, Command)
    assert result.update["current_builder"].name == "Test Hero"
    assert result.update["current_builder"].job == JobType.FIGHTER
    assert isinstance(result.update["messages"][0], ToolMessage)
    assert "saved" in result.update["messages"][0].content.lower()


def test_save_base_character_update(mock_tool_runtime: Callable[[dict], Any]) -> None:
    """Test updating an existing base character preserves selections."""
    existing_builder = CharacterBuilder(
        name="Old Name",
        icon="⚔️",
        job=JobType.FIGHTER,
    )
    existing_builder.selections.skill_proficiencies = [SkillType.ATHLETICS, SkillType.INTIMIDATION]

    runtime = mock_tool_runtime(
        {
            "current_builder": existing_builder,
            "party": [],
            "max_players": 2,
        }
    )

    updated_character = CharacterBuilder(
        name="New Name",
        icon="⚔️",
        job=JobType.FIGHTER,
    )

    result = save_base_character.invoke({"character": updated_character, "runtime": runtime})

    assert isinstance(result, Command)
    assert result.update["current_builder"].name == "New Name"
    # Selections preserved
    assert result.update["current_builder"].selections.skill_proficiencies == [
        SkillType.ATHLETICS,
        SkillType.INTIMIDATION,
    ]


def test_save_base_character_command_format(mock_tool_runtime: Callable[[dict], Any]) -> None:
    """Test save_base_character returns proper Command structure."""
    runtime = mock_tool_runtime(
        {
            "current_builder": None,
            "party": [],
            "max_players": 2,
        }
    )

    character = CharacterBuilder(name="Hero", icon="⚔️", job=JobType.FIGHTER)

    result = save_base_character.invoke({"character": character, "runtime": runtime})

    assert isinstance(result, Command)
    assert "current_builder" in result.update
    assert "messages" in result.update
    assert len(result.update["messages"]) == 1
    assert isinstance(result.update["messages"][0], ToolMessage)
    assert result.update["messages"][0].tool_call_id == "test_call_123"


def test_save_skills_valid(mock_tool_runtime: Callable[[dict], Any]) -> None:
    """Test saving valid skill proficiencies."""
    builder = CharacterBuilder(name="Cleric", icon="✝️", job=JobType.CLERIC)

    runtime = mock_tool_runtime(
        {
            "current_builder": builder,
            "party": [],
            "max_players": 2,
        }
    )

    selections = CharacterSelections(skill_proficiencies=[SkillType.HISTORY, SkillType.MEDICINE])

    result = save_skills.invoke({"selections": selections, "runtime": runtime})

    assert isinstance(result, Command)
    assert result.update["current_builder"].selections.skill_proficiencies == [
        SkillType.HISTORY,
        SkillType.MEDICINE,
    ]
    assert "Skills set" in result.update["messages"][0].content


def test_save_skills_invalid_skill(mock_tool_runtime: Callable[[dict], Any]) -> None:
    """Test saving invalid skill choice."""
    builder = CharacterBuilder(name="Cleric", icon="✝️", job=JobType.CLERIC)

    runtime = mock_tool_runtime(
        {
            "current_builder": builder,
            "party": [],
            "max_players": 2,
        }
    )

    # Athletics is not in Cleric's skill options
    selections = CharacterSelections(skill_proficiencies=[SkillType.ATHLETICS, SkillType.INTIMIDATION])

    result = save_skills.invoke({"selections": selections, "runtime": runtime})

    assert isinstance(result, Command)
    # Should return error message
    assert "Invalid skill" in result.update["messages"][0].content or "choices" in result.update["messages"][0].content


def test_save_skills_wrong_count(mock_tool_runtime: Callable[[dict], Any]) -> None:
    """Test saving wrong number of skills."""
    builder = CharacterBuilder(name="Cleric", icon="✝️", job=JobType.CLERIC)

    runtime = mock_tool_runtime(
        {
            "current_builder": builder,
            "party": [],
            "max_players": 2,
        }
    )

    # Cleric needs 2 skills, only providing 1
    selections = CharacterSelections(skill_proficiencies=[SkillType.HISTORY])

    result = save_skills.invoke({"selections": selections, "runtime": runtime})

    assert isinstance(result, Command)
    # Should return error message about count
    assert "2 skills" in result.update["messages"][0].content or "exactly" in result.update["messages"][0].content


def test_save_skills_no_builder(mock_tool_runtime: Callable[[dict], Any]) -> None:
    """Test save_skills when no current_builder exists."""
    runtime = mock_tool_runtime(
        {
            "current_builder": None,
            "party": [],
            "max_players": 2,
        }
    )

    selections = CharacterSelections(skill_proficiencies=[SkillType.ATHLETICS])

    result = save_skills.invoke({"selections": selections, "runtime": runtime})

    assert isinstance(result, Command)
    assert "No character" in result.update["messages"][0].content


def test_save_subclass_valid(mock_tool_runtime: Callable[[dict], Any]) -> None:
    """Test saving valid subclass choice."""
    builder = CharacterBuilder(name="Cleric", icon="✝️", job=JobType.CLERIC)

    runtime = mock_tool_runtime(
        {
            "current_builder": builder,
            "party": [],
            "max_players": 2,
        }
    )

    selections = CharacterSelections(subclass="life_domain")

    result = save_subclass.invoke({"selections": selections, "runtime": runtime})

    assert isinstance(result, Command)
    assert result.update["current_builder"].selections.subclass == "life_domain"
    assert "Subclass set" in result.update["messages"][0].content


def test_save_subclass_no_builder(mock_tool_runtime: Callable[[dict], Any]) -> None:
    """Test save_subclass when no current_builder exists."""
    runtime = mock_tool_runtime(
        {
            "current_builder": None,
            "party": [],
            "max_players": 2,
        }
    )

    selections = CharacterSelections(subclass="life_domain")

    result = save_subclass.invoke({"selections": selections, "runtime": runtime})

    assert isinstance(result, Command)
    assert "No character" in result.update["messages"][0].content


def test_save_equipment_valid(mock_tool_runtime: Callable[[dict], Any]) -> None:
    """Test saving valid equipment to correct slots."""
    builder = CharacterBuilder(name="Cleric", icon="✝️", job=JobType.CLERIC)

    runtime = mock_tool_runtime(
        {
            "current_builder": builder,
            "party": [],
            "max_players": 2,
        }
    )

    armor = Armor(name="Chain Mail", armor_type=ArmorType.HEAVY, base_ac=16)

    selections = CharacterSelections(equipment={EquipmentSlot.ARMOR: armor})

    result = save_starting_equipment.invoke({"selections": selections, "runtime": runtime})

    assert isinstance(result, Command)
    assert EquipmentSlot.ARMOR in result.update["current_builder"].selections.equipment
    assert result.update["current_builder"].selections.equipment[EquipmentSlot.ARMOR].name == "Chain Mail"
    assert "Starting equipment set" in result.update["messages"][0].content


def test_save_equipment_multiple_calls(mock_tool_runtime: Callable[[dict], Any]) -> None:
    """Test multiple save_starting_equipment calls accumulate equipment."""
    builder = CharacterBuilder(name="Cleric", icon="✝️", job=JobType.CLERIC)
    armor = Armor(name="Chain Mail", armor_type=ArmorType.HEAVY, base_ac=16)
    builder.selections.equipment[EquipmentSlot.ARMOR] = armor

    runtime = mock_tool_runtime(
        {
            "current_builder": builder,
            "party": [],
            "max_players": 2,
        }
    )

    # Add another piece of equipment
    mace = MeleeWeapon(
        name="Mace",
        weapon_type=WeaponType.SIMPLE_MELEE,
        handling=WeaponHandling.ONE_HANDED,
        ability=AbilityType.STR,
        damage_dice="1d6",
        damage_type=DamageType.BLUDGEONING,
    )

    selections = CharacterSelections(equipment={EquipmentSlot.MAIN_HAND: mace})

    result = save_starting_equipment.invoke({"selections": selections, "runtime": runtime})

    assert isinstance(result, Command)
    # Both equipment pieces should be present
    assert EquipmentSlot.ARMOR in result.update["current_builder"].selections.equipment
    assert EquipmentSlot.MAIN_HAND in result.update["current_builder"].selections.equipment


def test_save_equipment_no_builder(mock_tool_runtime: Callable[[dict], Any]) -> None:
    """Test save_starting_equipment when no current_builder exists."""
    runtime = mock_tool_runtime(
        {
            "current_builder": None,
            "party": [],
            "max_players": 2,
        }
    )

    armor = Armor(name="Chain Mail", armor_type=ArmorType.HEAVY, base_ac=16)
    selections = CharacterSelections(equipment={EquipmentSlot.ARMOR: armor})

    result = save_starting_equipment.invoke({"selections": selections, "runtime": runtime})

    assert isinstance(result, Command)
    assert "No character" in result.update["messages"][0].content


def test_finalize_character_complete(mock_tool_runtime: Callable[[dict], Any]) -> None:
    """Test finalizing a complete character."""
    builder = CharacterBuilder(name="Fighter", icon="⚔️", job=JobType.FIGHTER)
    builder.selections.skill_proficiencies = [SkillType.ATHLETICS, SkillType.INTIMIDATION]
    # Fighter doesn't require equipment or subclass for this test

    runtime = mock_tool_runtime(
        {
            "current_builder": builder,
            "party": [],
            "max_players": 2,
        }
    )

    result = finalize_character.invoke({"runtime": runtime})

    assert isinstance(result, Command)
    assert result.update["current_builder"] is None  # Reset after finalize
    assert result.update["party"] == [builder]
    assert "complete" in result.update["messages"][0].content.lower()


def test_finalize_character_auto_done(mock_tool_runtime: Callable[[dict], Any]) -> None:
    """Test finalize_character sets done=True when reaching max_players."""
    builder = CharacterBuilder(name="Fighter", icon="⚔️", job=JobType.FIGHTER)
    builder.selections.skill_proficiencies = [SkillType.ATHLETICS, SkillType.INTIMIDATION]

    # Party already has 1 character, finalizing 2nd reaches max
    existing_char = CharacterBuilder(name="Existing", icon="🧙", job=JobType.WIZARD)

    runtime = mock_tool_runtime(
        {
            "current_builder": builder,
            "party": [existing_char],
            "max_players": 2,
        }
    )

    result = finalize_character.invoke({"runtime": runtime})

    assert isinstance(result, Command)
    assert result.update["done"] is True  # Auto-done when reaching max


def test_get_party_status(mock_tool_runtime: Callable[[dict], Any]) -> None:
    """Test get_party_status returns summary."""
    char1 = CharacterBuilder(name="Hero1", icon="⚔️", job=JobType.FIGHTER, summary="A brave warrior")

    runtime = mock_tool_runtime(
        {
            "current_builder": None,
            "party": [char1],
            "max_players": 2,
        }
    )

    result = get_party_status.invoke({"runtime": runtime})

    assert "1/2" in result
    assert "Hero1" in result
    assert "brave warrior" in result
    assert "1 more" in result


def test_finalize_party(mock_tool_runtime: Callable[[dict], Any]) -> None:
    """Test finalize_party sets done=True."""
    char1 = CharacterBuilder(name="Hero1", icon="⚔️", job=JobType.FIGHTER, summary="A brave warrior")

    runtime = mock_tool_runtime(
        {
            "current_builder": None,
            "party": [char1],
            "max_players": 2,
        }
    )

    result = finalize_party.invoke({"runtime": runtime})

    assert isinstance(result, Command)
    assert result.update["done"] is True
    assert "Party complete" in result.update["messages"][0].content
    assert "Hero1" in result.update["messages"][0].content
