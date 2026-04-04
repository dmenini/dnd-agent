"""Tests for JobService."""

from agent.character.abilities import AbilityType
from agent.character.character import Character
from agent.character.resources import SpellLevel
from agent.jobs.cleric import Cleric
from agent.jobs.wizard import Wizard
from agent.services.job_service import JobService


def test_apply_job_features(fighter: Character) -> None:
    """Test that job features are properly applied."""
    # Fighter starts with job features applied
    assert len(fighter.special_abilities) > 0
    assert any(a.name == "Second Wind" for a in fighter.special_abilities)


def test_change_job(fighter: Character) -> None:
    """Test changing character's job."""
    # Fighter starts with Fighter job
    assert fighter.job.type.value == "fighter"
    initial_features = {a.id for a in fighter.special_abilities}

    # Change to Wizard
    JobService.change_job(fighter, Wizard)

    assert fighter.job.type.value == "wizard"
    assert fighter.attributes.spellcasting_ability == AbilityType.INT

    # Should have different abilities now
    new_features = {a.id for a in fighter.special_abilities}
    assert new_features != initial_features

    # Fighter abilities should be gone
    assert not any(a.name == "Second Wind" for a in fighter.special_abilities)

    # Wizard abilities should be present
    assert any(a.name == "Arcane Recovery" for a in fighter.special_abilities)


def test_change_job_updates_proficiencies(fighter: Character) -> None:
    """Test that changing jobs updates proficiencies."""
    initial_profs = len(fighter.attributes.proficiencies)

    # Change to Wizard (different proficiencies)
    JobService.change_job(fighter, Wizard)

    # Proficiency count should be different
    new_profs = len(fighter.attributes.proficiencies)
    assert new_profs != initial_profs


def test_change_job_updates_spell_slots(fighter: Character) -> None:
    """Test that changing jobs updates spell slot progression."""
    # Fighter has no spell slots
    assert len(fighter.spell_slots.max_slots) == 0 or all(v == 0 for v in fighter.spell_slots.max_slots.values())

    # Change to Wizard
    JobService.change_job(fighter, Wizard)

    # Should now have spell slots for a level 5 wizard
    assert fighter.spell_slots.max_slots.get(SpellLevel.LEVEL_1, 0) > 0  # 1st level slots
    assert fighter.spell_slots.max_slots.get(SpellLevel.LEVEL_2, 0) > 0  # 2nd level slots
    assert fighter.spell_slots.max_slots.get(SpellLevel.LEVEL_3, 0) > 0  # 3rd level slots


def test_apply_job_features_adds_spells(wizard: Character) -> None:
    """Test that job features include spells for casters."""
    # Wizard should have spells from their job
    assert len(wizard.spells) > 0


def test_change_job_removes_spells(wizard: Character) -> None:
    """Test that changing jobs removes old spells."""
    initial_spells = len(wizard.spells)
    assert initial_spells > 0

    # Change to Cleric (different spell list)
    JobService.change_job(wizard, Cleric)

    # Should have Cleric spells now
    new_spells = len(wizard.spells)
    assert new_spells > 0

    # Spells should be different - Cleric should have Sacred Flame
    assert any(s.name == "Sacred Flame" for s in wizard.spells)


def test_apply_job_features_sets_spellcasting_ability(wizard: Character) -> None:
    """Test that spellcasting ability is set correctly."""
    assert wizard.attributes.spellcasting_ability == AbilityType.INT

    # Change to Cleric
    JobService.change_job(wizard, Cleric)

    assert wizard.attributes.spellcasting_ability == AbilityType.WIS


def test_apply_job_features_sets_hit_die(fighter: Character) -> None:
    """Test that hit die is set from job."""
    assert fighter.attributes.hit_die == 10  # Fighter hit die

    JobService.change_job(fighter, Wizard)

    assert fighter.attributes.hit_die == 6  # Wizard hit die
