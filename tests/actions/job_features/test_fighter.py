from unittest.mock import MagicMock

from agent.actions.jobs.fighter import SecondWindAction
from agent.character.character import Character
from agent.jobs.features import FeatureId
from agent.mechanics.dice_roller import DiceRoll


def test_second_wind(actor: Character) -> None:
    start_hp = 1
    actor.attributes.hp = start_hp
    actor.level = 1

    action = SecondWindAction(id=FeatureId.SECOND_WIND.value, description="")

    amount = 5
    actor._dice = MagicMock()
    actor._dice.roll_once.return_value = DiceRoll(expression="1d10", rolls=[amount], total=amount, raw=amount)

    action.execute(actor, actor)

    # Assert healing is deterministic (5 from roll + 1 from level)
    assert actor.attributes.hp == start_hp + amount + actor.level
