from unittest.mock import MagicMock

from agent.character.character import Character
from agent.jobs.fighter import Fighter
from agent.mechanics.dice_roller import DiceRoll
from agent.models.constants import FeatureId


def test_second_wind(actor: Character) -> None:
    actor.job = Fighter
    actor.apply_job_features()

    # Verify active action is available
    assert any(a.id == FeatureId.SECOND_WIND_ID for a in actor.abilities)

    start_hp = 1
    actor.attributes.hp = start_hp
    actor.level = 1

    amount = 5
    actor._dice = MagicMock()
    actor._dice.roll_once.return_value = DiceRoll(expression="1d10", rolls=[amount], total=amount, raw=amount)

    # Use Second Wind
    action = next(a for a in actor.abilities if a.id == FeatureId.SECOND_WIND_ID)
    action.execute(actor, None)

    # Assert healing is deterministic (5 from roll + 1 from level)
    assert actor.attributes.hp == start_hp + amount + actor.level
