from agent.actions.jobs.cleric import DivineRestorationAction
from agent.character.character import Character
from agent.jobs.cleric import Cleric
from agent.models.context import CombatContext
from agent.models.enums import FeatureId


def test_divine_restoration(actor: Character, target: Character) -> None:
    actor.change_job(Cleric)
    actor.level = 3
    target.attributes.hp = 1

    action = DivineRestorationAction(id=FeatureId.DIVINE_RESTORATION.value, description="")

    action.execute(actor, target, ctx=CombatContext())

    assert target.attributes.hp > 1

    # Finalize action consumes the bonus use
    action.finalize(actor)
    assert action.is_available(actor.action_economy) is False
    assert action.current_uses == 1
