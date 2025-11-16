from pytest_mock import MockerFixture

from agent.actions.jobs.cleric import DivineRestorationAction, PreserveLifeAction
from agent.character.character import Character
from agent.jobs.cleric import Cleric, LifeDomain
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


def test_preserve_life(actor: Character, target: Character, mocker: MockerFixture) -> None:
    actor.change_job(Cleric.apply_specialization(LifeDomain))
    actor.level = 4  # 4 * 5 = 20 HP to distribute
    target.attributes.hp = 1
    target.attributes.max_hp = lambda level: 50  # Half would be 25

    action = PreserveLifeAction(id=FeatureId.PRESERVE_LIFE.value, description="")

    # Create a combat context with one target receiving healing
    ctx = CombatContext()
    ctx.hits = {target.id: 1}  # Simulate one target being healed

    action.execute(actor, target, ctx)

    # Should heal for 20 HP (total pool) but capped at 25 (half of max_hp)
    # Since target is at 1 HP, healing should bring them to 21 HP
    assert target.attributes.hp == 21

    # Finalize action consumes the bonus use
    action.finalize(actor)
    assert action.is_available(actor.action_economy) is False
    assert action.current_uses == 1
