from agent.character.character import Character
from agent.jobs.wizard import Wizard
from agent.models.enums import FeatureId
from agent.services.job_service import JobService


def test_mage(actor: Character) -> None:
    # Setup actor as a Mage and apply features
    actor.equipment.armor = None
    JobService.change_job(actor, Wizard)

    abilities = [a.id for a in actor.special_abilities]
    assert FeatureId.ARCANE_RECOVERY in abilities

    spells = [a.id for a in actor.spells]
    assert FeatureId.MAGIC_MISSILE in spells

    assert any(t.feature_id == FeatureId.AC_BONUS_WITHOUT_ARMOR for t in actor.passives)
    assert actor.attributes.get_modifiers("ac")[0].value == 3


def test_wizard_serialization(actor: Character) -> None:
    JobService.change_job(actor, Wizard)

    # Test round-trip serialization
    actor_dict = actor.model_dump()
    actor2 = Character.model_validate(actor_dict)
    assert actor2.model_dump() == actor_dict

    # Verify key attributes are preserved
    assert len(actor2.spells) == len(actor.spells)
    assert actor2.spells[0].id == actor.spells[0].id
    assert actor2.spells[0].name == actor.spells[0].name
