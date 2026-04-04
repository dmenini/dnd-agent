from agent.character.character import Character
from agent.jobs.rogue import Rogue
from agent.models.enums import FeatureId
from agent.services.job_service import JobService


def test_rogue(actor: Character) -> None:
    JobService.change_job(actor, Rogue)

    assert any(t.feature_id == FeatureId.DAMAGE_BONUS_WITH_ADVANTAGE for t in actor.passives)
    assert sum(t.feature_id == FeatureId.EXPERTISE for t in actor.passives) == 2


def test_rogue_serialization(actor: Character) -> None:
    JobService.change_job(actor, Rogue)

    actor_dict = actor.model_dump()
    actor2 = Character.model_validate(actor_dict)
    assert actor2.model_dump() == actor_dict

    assert actor2.passives == actor.passives
    assert actor2.special_abilities == actor.special_abilities
    assert actor2.attributes == actor.attributes
    assert actor2.spells == actor.spells
