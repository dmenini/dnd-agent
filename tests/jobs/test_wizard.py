from agent.character.character import Character
from agent.jobs.wizard import Wizard
from agent.models.enums import FeatureId
from agent.services.job_service import JobService


def test_mage(wizard: Character) -> None:
    abilities = [a.id for a in wizard.special_abilities]
    assert FeatureId.ARCANE_RECOVERY in abilities

    spells = [a.id for a in wizard.spells]
    assert FeatureId.MAGIC_MISSILE in spells

    assert any(t.feature_id == FeatureId.AC_BONUS_WITHOUT_ARMOR for t in wizard.passives)
    assert wizard.attributes.get_modifiers("ac")[0].value == 3


def test_wizard_serialization(wizard: Character) -> None:
    # Test round-trip serialization
    actor_dict = wizard.model_dump()
    actor2 = Character.model_validate(actor_dict)
    assert actor2.model_dump() == actor_dict

    # Verify key attributes are preserved
    assert len(actor2.spells) == len(wizard.spells)
    assert actor2.spells[0].id == wizard.spells[0].id
    assert actor2.spells[0].name == wizard.spells[0].name
