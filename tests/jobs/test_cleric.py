from agent.character.character import Character
from agent.equipment.armor import Armor, ArmorType
from agent.jobs.cleric import Cleric, LifeDomain
from agent.models.enums import FeatureId
from agent.services.job_service import JobService


def test_cleric(actor: Character) -> None:
    # Setup actor as a Cleric and apply features
    actor.equipment.armor = Armor(name="Glass", armor_type=ArmorType.LIGHT, base_ac=2)

    job = Cleric
    job = job.apply_specialization(LifeDomain)
    JobService.change_job(actor, job)

    abilities = [a.id for a in actor.special_abilities]
    assert FeatureId.PRESERVE_LIFE in abilities

    spells = [a.id for a in actor.spells]
    assert FeatureId.BLESS in spells
    assert FeatureId.SACRED_FLAME in spells

    assert any(t.feature_id == FeatureId.AC_BONUS_WITH_ARMOR_TYPES for t in actor.passives)
    assert actor.attributes.get_modifiers("ac")[0].value == 1

    assert any(t.feature_id == FeatureId.HEALING_BONUS for t in actor.passives)


def test_cleric_serialization(actor: Character) -> None:
    JobService.change_job(actor, Cleric)

    # Test round-trip serialization
    actor_dict = actor.model_dump(mode="python")
    actor2 = Character.model_validate(actor_dict)

    # Compare dict representations (since discriminated unions may not preserve exact object identity)
    assert actor2.model_dump(mode="python") == actor_dict

    # Verify key attributes are preserved
    assert len(actor2.spells) == len(actor.spells)
    assert actor2.spells[0].id == actor.spells[0].id
    assert actor2.spells[0].name == actor.spells[0].name


def test_cleric_spell_level_gating() -> None:
    """Test that spells are properly gated by level."""
    # Level 1 cleric should only have level 1 spells
    level_1_spells = Cleric.get_spells_for_level(1)
    assert len(level_1_spells) == 1  # Only Sacred Flame
    assert all((spell.level_required or 1) <= 1 for spell in level_1_spells)

    # Level 3 cleric should have all spells
    level_3_spells = Cleric.get_spells_for_level(3)
    assert len(level_3_spells) == 1  # Sacred Flame (no level 3 spells in base cleric)

    # Apply Life Domain specialization

    life_cleric = Cleric.apply_specialization(LifeDomain)

    # Level 1 Life cleric
    level_1_spells = life_cleric.get_spells_for_level(1)
    level_1_names = {spell.name for spell in level_1_spells}
    assert "Sacred Flame" in level_1_names
    assert "Cure Wounds" in level_1_names
    assert "Bless" in level_1_names
    assert "Lesser Restoration" not in level_1_names  # Level 3 spell

    # Level 3 Life cleric should have all spells
    level_3_spells = life_cleric.get_spells_for_level(3)
    level_3_names = {spell.name for spell in level_3_spells}
    assert "Sacred Flame" in level_3_names
    assert "Cure Wounds" in level_3_names
    assert "Bless" in level_3_names
    assert "Lesser Restoration" in level_3_names  # Now available!
