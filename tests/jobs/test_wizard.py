from agent.character.character import Character
from agent.jobs.wizard import Wizard
from agent.models.enums import FeatureId


def test_mage(actor: Character) -> None:
    # Setup actor as a Mage and apply features
    actor.equipment.armor = None
    actor.change_job(Wizard)

    abilities = [a.id for a in actor.special_abilities]
    assert FeatureId.ARCANE_RECOVERY in abilities

    spells = [a.id for a in actor.spells]
    assert FeatureId.MAGIC_MISSILE in spells

    assert any(t.feature_id == FeatureId.AC_BONUS_WITHOUT_ARMOR for t in actor.passives)
    assert actor.attributes.get_modifiers("ac")[0].value == 3


def test_wizard_serialization(actor: Character) -> None:
    actor.change_job(Wizard)

    actor_dict = actor.model_dump()
    actor2 = Character.model_validate(actor_dict)
    assert actor2.model_dump() == actor_dict

    assert actor2.passives == actor.passives
    assert actor2.special_abilities == actor.special_abilities
    assert actor2.attributes == actor.attributes
    assert actor2.spells == actor.spells
