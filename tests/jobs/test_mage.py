from agent.character.character import Character
from agent.jobs.features import FeatureId
from agent.jobs.mage import Mage


def test_mage(actor: Character) -> None:
    # Setup actor as a Mage and apply features
    actor.job = Mage
    actor.apply_job_features()

    # Verify Arcane Recovery action is available
    action = next(a for a in actor.abilities if a.id == FeatureId.ARCANE_RECOVERY)
    assert action is not None
