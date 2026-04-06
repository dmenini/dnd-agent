from agent.character.character import Character
from agent.equipment.armor import Armor, ArmorType
from agent.jobs.fighter import Fighter
from agent.models.enums import FeatureId
from agent.services.job_service import JobService


def test_fighter(actor: Character) -> None:
    actor.equipment.armor = Armor(name="Armor", armor_type=ArmorType.HEAVY, base_ac=5)
    JobService.change_job(actor, Fighter)

    # Verify active action is available
    assert any(a.id == FeatureId.SECOND_WIND for a in actor.special_abilities)

    assert any(t.feature_id == FeatureId.AC_BONUS_WITH_ARMOR for t in actor.passives)
    assert actor.attributes.get_modifiers("ac")[0].value == 1


def test_fighter_serialization(actor: Character) -> None:
    JobService.change_job(actor, Fighter)

    # Test round-trip serialization
    actor_dict = actor.model_dump()
    actor2 = Character.model_validate(actor_dict)
    assert actor2.model_dump() == actor_dict

    # Verify key attributes are preserved
    assert len(actor2.special_abilities) == len(actor.special_abilities)
    if actor.special_abilities:
        assert actor2.special_abilities[0].id == actor.special_abilities[0].id
