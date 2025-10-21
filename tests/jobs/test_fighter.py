from agent.character.character import Character
from agent.jobs.feature import FeatureId
from agent.jobs.fighter import Fighter


def test_fighter(actor: Character) -> None:
    actor.change_job(Fighter)

    # Verify active action is available
    assert any(a.id == FeatureId.SECOND_WIND for a in actor.abilities)
