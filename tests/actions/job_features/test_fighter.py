from agent.actions.registry import ActionRegistry
from agent.character.character import Character
from agent.models.context import CombatContext
from agent.models.enums import FeatureId
from tests.conftest import cheater_dice


def test_second_wind(actor: Character) -> None:
    start_hp = 1
    actor.attributes.hp = start_hp
    actor.level = 1

    action = ActionRegistry.create(FeatureId.SECOND_WIND)

    # Set dice to roll 5 for healing
    actor.cheater_dice = cheater_dice(value=5)

    action.execute(actor, actor, ctx=CombatContext())

    # Assert healing is deterministic (5 from roll + 1 from level)
    assert actor.attributes.hp == start_hp + 5 + actor.level
