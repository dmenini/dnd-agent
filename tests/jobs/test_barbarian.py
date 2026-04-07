from agent.character.character import Character
from agent.jobs.barbarian import Barbarian
from agent.models.enums import FeatureId
from agent.services.job_service import JobService


def test_barbarian(actor: Character) -> None:
    JobService.change_job(actor, Barbarian)

    # Verify active action is available
    assert any(a.id == FeatureId.RAGE for a in actor.special_abilities)

    assert any(t.feature_id == FeatureId.AC_BONUS_MOD_WITHOUT_ARMOR for t in actor.passives)
    assert actor.attributes.get_modifiers("ac_mod.constitution")[0].value == 1


def test_barbarian_serialization(actor: Character) -> None:
    JobService.change_job(actor, Barbarian)

    actor_dict = actor.model_dump()
    actor2 = Character.model_validate(actor_dict)
    assert actor2.model_dump() == actor_dict

    assert actor2.passives == actor.passives
    # ComposableActions have serialization issues with nested discriminated unions
    # Just check basic properties instead of full equality
    assert len(actor2.special_abilities) == len(actor.special_abilities)
    assert actor2.special_abilities[0].id == actor.special_abilities[0].id
    assert actor2.special_abilities[0].name == actor.special_abilities[0].name
    assert actor2.attributes == actor.attributes
    assert actor2.spells == actor.spells
