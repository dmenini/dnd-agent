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
    assert FeatureId.DIVINE_RESTORATION in abilities

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
