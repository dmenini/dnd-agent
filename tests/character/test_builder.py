"""Tests for CharacterBuilder and character creation flow."""

import pytest

from agent.character.abilities import Abilities, AbilityType, SkillType
from agent.character.builder import CharacterBuilder, CharacterSelections
from agent.equipment.armor import Armor, ArmorType
from agent.equipment.base import EquipmentSlot
from agent.equipment.weapons import MeleeWeapon, WeaponHandling, WeaponType
from agent.jobs.base import JobType
from agent.jobs.feature import EquipmentChoice, OptionItem
from agent.models.damage import DamageType

# No ClericDomain enum exists - domains are strings


def test_character_builder_validates_ability_scores() -> None:
    """Test that character builder validates total ability scores."""
    # Valid scores (total < MAX_SCORES_TOTAL)
    builder = CharacterBuilder(
        name="Test",
        icon="⚔️",
        job=JobType.FIGHTER,
        abilities=Abilities(strength=15, dexterity=14, constitution=13, intelligence=12, wisdom=10, charisma=8),
    )
    assert builder.abilities.strength == 15

    # Invalid scores (total > MAX_SCORES_TOTAL)
    with pytest.raises(ValueError, match="total scores must be lower"):
        CharacterBuilder(
            name="Test",
            icon="⚔️",
            job=JobType.FIGHTER,
            abilities=Abilities(strength=18, dexterity=18, constitution=18, intelligence=18, wisdom=18, charisma=18),
        )


def test_character_builder_to_character_basic() -> None:
    """Test converting CharacterBuilder to Character with minimal selections."""
    builder = CharacterBuilder(
        name="Aragorn",
        icon="🗡️",
        job=JobType.FIGHTER,
        race="human",
        backstory="A ranger from the north",
        abilities=Abilities(strength=15, dexterity=14, constitution=13, intelligence=10, wisdom=10, charisma=8),
    )

    character = builder.to_character(party="Fellowship")

    assert character.name == "Aragorn"
    assert character.icon == "🗡️"
    assert character.id == "aragorn"
    assert character.is_player is True
    assert character.party.name == "Fellowship"
    assert character.party.is_player_party is True
    assert character.attributes.strength == 15
    assert character.narrative.backstory == "A ranger from the north"
    assert character.narrative.race == "human"


def test_character_builder_to_character_with_skill_selections() -> None:
    """Test converting CharacterBuilder with skill proficiency selections."""
    builder = CharacterBuilder(
        name="Test Fighter",
        icon="⚔️",
        job=JobType.FIGHTER,
        abilities=Abilities(strength=15, dexterity=14, constitution=13, intelligence=10, wisdom=10, charisma=8),
    )
    builder.selections.skill_proficiencies = [SkillType.ATHLETICS, SkillType.INTIMIDATION]

    character = builder.to_character(party="Adventurers")

    # Check skill proficiencies specifically (job adds other proficiencies too)
    skill_profs = [p for p in character.attributes.proficiencies if p.type.value == "skill"]
    assert len(skill_profs) == 2
    assert any(p.target == SkillType.ATHLETICS for p in skill_profs)
    assert any(p.target == SkillType.INTIMIDATION for p in skill_profs)


def test_character_builder_to_character_with_equipment_selections() -> None:
    """Test converting CharacterBuilder with equipment selections."""
    builder = CharacterBuilder(
        name="Test Fighter",
        icon="⚔️",
        job=JobType.FIGHTER,
        abilities=Abilities(strength=15, dexterity=14, constitution=13, intelligence=10, wisdom=10, charisma=8),
    )

    longsword = MeleeWeapon(
        name="Longsword",
        weapon_type=WeaponType.MARTIAL_MELEE,
        handling=WeaponHandling.VERSATILE,
        ability=AbilityType.STR,
        damage_dice="1d8",
        versatile_damage="1d10",
        damage_type=DamageType.SLASHING,
    )

    leather_armor = Armor(
        name="Leather Armor",
        armor_type=ArmorType.LIGHT,
        base_ac=11,
    )

    builder.selections.equipment = {
        EquipmentSlot.MAIN_HAND: longsword,
        EquipmentSlot.ARMOR: leather_armor,
    }

    character = builder.to_character(party="Adventurers")

    assert character.equipment.armor is not None
    assert character.equipment.armor.name == "Leather Armor"
    assert character.equipment.main_hand is not None
    assert character.equipment.main_hand.name == "Longsword"


def test_character_builder_to_character_with_subclass() -> None:
    """Test converting CharacterBuilder with subclass selection."""
    builder = CharacterBuilder(
        name="Test Cleric",
        icon="✝️",
        job=JobType.CLERIC,
        abilities=Abilities(strength=10, dexterity=12, constitution=14, intelligence=10, wisdom=15, charisma=10),
    )
    builder.selections.subclass = "life_domain"

    character = builder.to_character(party="Healers")

    assert character.job.specialization == "Life Domain"
    # Life domain should have additional features
    assert len(character.job.features) > 0


def test_character_selections_validate_skills_valid() -> None:
    """Test skill validation with valid choices."""
    selections = CharacterSelections()
    selections.skill_proficiencies = [SkillType.ATHLETICS, SkillType.PERCEPTION]

    # Should not raise
    selections.validate_skills(
        options=[SkillType.ATHLETICS, SkillType.PERCEPTION, SkillType.SURVIVAL, SkillType.INTIMIDATION],
        max_count=2,
    )


def test_character_selections_validate_skills_invalid_skill() -> None:
    """Test skill validation with invalid skill choice."""
    selections = CharacterSelections()
    selections.skill_proficiencies = [SkillType.ATHLETICS, SkillType.ARCANA]  # ARCANA not in options

    with pytest.raises(ValueError, match="Invalid skill choices"):
        selections.validate_skills(
            options=[SkillType.ATHLETICS, SkillType.PERCEPTION, SkillType.SURVIVAL],
            max_count=2,
        )


def test_character_selections_validate_skills_wrong_count() -> None:
    """Test skill validation with wrong number of skills."""
    selections = CharacterSelections()
    selections.skill_proficiencies = [SkillType.ATHLETICS]  # Only 1, need 2

    with pytest.raises(ValueError, match="Must choose exactly 2 skills"):
        selections.validate_skills(
            options=[SkillType.ATHLETICS, SkillType.PERCEPTION, SkillType.SURVIVAL],
            max_count=2,
        )


def test_character_selections_validate_equipment_valid() -> None:
    """Test equipment validation with valid choices."""
    longsword = MeleeWeapon(
        name="Longsword",
        weapon_type=WeaponType.MARTIAL_MELEE,
        handling=WeaponHandling.VERSATILE,
        ability=AbilityType.STR,
        damage_dice="1d8",
        damage_type=DamageType.SLASHING,
    )

    selections = CharacterSelections()
    selections.equipment = {
        EquipmentSlot.MAIN_HAND: longsword,
    }

    options = [
        EquipmentChoice(
            slot=EquipmentSlot.MAIN_HAND,
            options=[
                OptionItem(id="longsword", name="Longsword"),
                OptionItem(id="battleaxe", name="Battleaxe"),
            ],
            description="Choose a weapon",
        ),
    ]

    # Should not raise
    selections.validate_equipment_choices(options)


def test_character_selections_validate_equipment_invalid_slot() -> None:
    """Test equipment validation with invalid slot."""
    longsword = MeleeWeapon(
        name="Longsword",
        weapon_type=WeaponType.MARTIAL_MELEE,
        handling=WeaponHandling.VERSATILE,
        ability=AbilityType.STR,
        damage_dice="1d8",
        damage_type=DamageType.SLASHING,
    )

    selections = CharacterSelections()
    selections.equipment = {
        EquipmentSlot.OFF_HAND: longsword,  # Not in options
    }

    options: list[EquipmentChoice] = []  # Empty options

    with pytest.raises(ValueError, match="Invalid equipment slot"):
        selections.validate_equipment_choices(options)


def test_character_builder_string_representation() -> None:
    """Test CharacterBuilder string representation."""
    builder = CharacterBuilder(
        name="Gandalf",
        icon="🧙",
        job=JobType.WIZARD,
        race="maia",
    )

    assert str(builder) == "🧙 Gandalf - Maia Wizard"


def test_character_builder_with_all_narrative_fields() -> None:
    """Test CharacterBuilder with all narrative attributes."""
    builder = CharacterBuilder(
        name="Legolas",
        icon="🏹",
        job=JobType.FIGHTER,
        race="elf",
        backstory="Prince of the Woodland Realm",
        personality="Graceful and deadly",
        alignment="Lawful Good",
        summary="Elven archer with unmatched skill",
        abilities=Abilities(strength=13, dexterity=15, constitution=13, intelligence=10, wisdom=13, charisma=8),
    )

    character = builder.to_character(party="Fellowship")

    assert character.narrative.race == "elf"
    assert character.narrative.backstory == "Prince of the Woodland Realm"
    assert character.narrative.personality == "Graceful and deadly"
    assert character.narrative.alignment == "Lawful Good"
    assert character.narrative.summary == "Elven archer with unmatched skill"


def test_character_builder_default_values() -> None:
    """Test CharacterBuilder with default values."""
    builder = CharacterBuilder(
        name="Simple Hero",
        icon="⚔️",
        job=JobType.FIGHTER,
    )

    assert builder.race == "human"
    assert builder.backstory == ""
    assert builder.personality == ""
    assert builder.alignment == ""
    assert builder.summary == ""
    assert builder.abilities.strength == 10  # Default ability score
    assert builder.selections.skill_proficiencies == []
    assert builder.selections.equipment == {}
    assert builder.selections.subclass is None


def test_character_builder_multiple_jobs() -> None:
    """Test CharacterBuilder works with all job types."""
    jobs = [JobType.FIGHTER, JobType.WIZARD, JobType.CLERIC, JobType.BARBARIAN, JobType.ROGUE]

    for job_type in jobs:
        builder = CharacterBuilder(
            name=f"Test {job_type.value}",
            icon="⚔️",
            job=job_type,
            abilities=Abilities(strength=13, dexterity=13, constitution=13, intelligence=11, wisdom=11, charisma=11),
        )
        character = builder.to_character(party="Test Party")

        assert character.job.type == job_type
        assert character.name == f"Test {job_type.value}"
