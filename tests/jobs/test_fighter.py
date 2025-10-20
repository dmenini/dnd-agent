from agent.character.character import Character
from agent.jobs.features import FeatureId
from agent.jobs.fighter import Fighter


def test_fighter(actor: Character) -> None:
    actor.job = Fighter
    actor.apply_job_features()

    # Verify active action is available
    assert any(a.id == FeatureId.SECOND_WIND for a in actor.abilities)
