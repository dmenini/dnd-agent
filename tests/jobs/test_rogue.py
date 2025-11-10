from agent.character.character import Character
from agent.jobs.rogue import Rogue
from agent.models.enums import FeatureId


def test_rogue(actor: Character) -> None:
    actor.change_job(Rogue)

    assert any(t.feature_id == FeatureId.DAMAGE_BONUS_WITH_ADVANTAGE for t in actor.passives)
    assert sum(t.feature_id == FeatureId.EXPERTISE for t in actor.passives) == 2
