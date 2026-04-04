from agent.character.character import Character
from agent.character.resources import SpellLevel
from agent.jobs.cleric import Cleric, WarDomain
from agent.jobs.wizard import Wizard
from agent.models.enums import FeatureId
from agent.services.job_service import JobService
from agent.services.level_service import LevelService


def test_level_up_increases_level_and_hp(actor: Character) -> None:
    """Test that leveling up increases level and HP correctly."""
    job = Wizard
    JobService.change_job(actor, job)

    # Set to level 1
    actor.level = 1
    actor.attributes.hp = actor.max_hp
    old_hp = actor.attributes.hp
    old_max_hp = actor.max_hp

    # Level up
    LevelService.level_up(actor)

    assert actor.level == 2
    assert actor.max_hp > old_max_hp
    assert actor.attributes.hp > old_hp  # HP should increase


def test_level_up_applies_new_features(actor: Character) -> None:
    """Test that leveling up applies features at the correct level."""
    job = Cleric.apply_specialization(WarDomain)
    JobService.change_job(actor, job)

    # Start at level 1
    actor.level = 1
    JobService.apply_job_features(actor)

    # War Priest should be available at level 1
    abilities = [a.id for a in actor.special_abilities]
    assert FeatureId.WAR_PRIEST in abilities

    # No level 2 features yet
    # (Life Domain has Preserve Life at L2, but we're War Domain)

    # TODO: Add test once War Domain has a L2+ feature


def test_level_up_applies_new_spells(actor: Character) -> None:
    """Test that domain spells are learned at correct levels."""
    job = Cleric.apply_specialization(WarDomain)
    JobService.change_job(actor, job)

    # Start at level 1
    actor.level = 1
    JobService.apply_job_features(actor)

    # Should have level 1 spells
    spells = [s.id for s in actor.spells]
    assert FeatureId.DIVINE_FAVOR in spells
    assert FeatureId.SHIELD_OF_FAITH in spells

    # Level up to 3 (when level 3 domain spells become available)
    LevelService.set_level(actor, 3)

    # Should now have level 3 spells
    # TODO: Implement and test once we add level 3 War Domain spells


def test_proficiency_bonus_scales(actor: Character) -> None:
    """Test that proficiency bonus increases at levels 5, 9, 13, 17."""
    job = Wizard
    JobService.change_job(actor, job)

    # Level 1-4: +2
    actor.level = 1
    assert actor.attributes.proficiency_bonus(1) == 2
    assert actor.attributes.proficiency_bonus(4) == 2

    # Level 5-8: +3
    assert actor.attributes.proficiency_bonus(5) == 3
    assert actor.attributes.proficiency_bonus(8) == 3

    # Level 9-12: +4
    assert actor.attributes.proficiency_bonus(9) == 4
    assert actor.attributes.proficiency_bonus(12) == 4

    # Level 13-16: +5
    assert actor.attributes.proficiency_bonus(13) == 5
    assert actor.attributes.proficiency_bonus(16) == 5

    # Level 17-20: +6
    assert actor.attributes.proficiency_bonus(17) == 6
    assert actor.attributes.proficiency_bonus(20) == 6


def test_spell_slots_scale_with_level(actor: Character) -> None:
    """Test that spell slots increase as character levels up."""
    job = Wizard
    JobService.change_job(actor, job)

    # Level 1: 2 level-1 slots
    actor.level = 1
    actor.spell_slots.recompute(1)
    assert actor.spell_slots.max_slots[SpellLevel.LEVEL_1] == 2
    assert SpellLevel.LEVEL_2 not in actor.spell_slots.max_slots

    # Level 3: gains level-2 slots
    actor.level = 3
    actor.spell_slots.recompute(3)
    assert actor.spell_slots.max_slots[SpellLevel.LEVEL_1] == 4
    assert actor.spell_slots.max_slots[SpellLevel.LEVEL_2] == 2

    # Level 5: gains level-3 slots
    actor.level = 5
    actor.spell_slots.recompute(5)
    assert actor.spell_slots.max_slots[SpellLevel.LEVEL_1] == 4
    assert actor.spell_slots.max_slots[SpellLevel.LEVEL_2] == 3
    assert actor.spell_slots.max_slots[SpellLevel.LEVEL_3] == 2


def test_set_level_applies_all_features(actor: Character) -> None:
    """Test that set_level applies all features up to target level."""
    job = Cleric.apply_specialization(WarDomain)
    JobService.change_job(actor, job)

    # Start at level 1
    actor.level = 1
    JobService.apply_job_features(actor)

    # Jump to level 5
    LevelService.set_level(actor, 5)

    assert actor.level == 5
    assert actor.max_hp > actor.attributes.max_hp(1)

    # Should have all spells/features for levels 1-5
    spells = [s.id for s in actor.special_abilities]
    assert FeatureId.WAR_PRIEST in spells
