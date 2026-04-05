"""Test spell level gating."""

from agent.jobs.cleric import Cleric


def test_cleric_spell_level_gating():
    """Test that spells are properly gated by level."""
    # Level 1 cleric should only have level 1 spells
    level_1_spells = Cleric.get_spells_for_level(1)
    assert len(level_1_spells) == 1  # Only Sacred Flame
    assert all(spell.metadata.get("level_required", 1) <= 1 for spell in level_1_spells)

    # Level 3 cleric should have all spells
    level_3_spells = Cleric.get_spells_for_level(3)
    assert len(level_3_spells) == 1  # Sacred Flame (no level 3 spells in base cleric)

    # Apply Life Domain specialization
    from agent.jobs.cleric import LifeDomain
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

    print(f"\nLevel 1 Life Cleric spells: {len(level_1_spells)}")
    for spell in level_1_spells:
        print(f"  - {spell.name} (requires level {spell.metadata.get('level_required')})")

    print(f"\nLevel 3 Life Cleric spells: {len(level_3_spells)}")
    for spell in level_3_spells:
        print(f"  - {spell.name} (requires level {spell.metadata.get('level_required')})")
