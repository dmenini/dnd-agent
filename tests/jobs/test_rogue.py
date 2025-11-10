from agent.character.character import Character
from agent.jobs.rogue import Rogue
from agent.models.enums import FeatureId


def test_rogue(actor: Character) -> None:
    actor.change_job(Rogue)

    assert any(t.feature_id == FeatureId.DAMAGE_BONUS_WITH_ADVANTAGE for t in actor.passives)
    assert sum(t.feature_id == FeatureId.EXPERTISE for t in actor.passives) == 2


def test_rogue_serialization(actor: Character) -> None:
    actor.change_job(Rogue)

    actor_dict = actor.model_dump()
    actor2 = Character.model_validate(actor_dict)
    assert actor2.model_dump() == actor_dict

    assert actor2.passives == actor.passives
    assert actor2.special_abilities == actor.special_abilities
    assert actor2.attributes == actor.attributes
    assert actor2.spells == actor.spells
