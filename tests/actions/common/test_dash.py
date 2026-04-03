from agent.actions.common.dash import DashAction
from agent.character.character import Character
from agent.effects.base import Trait
from agent.models.context import CombatContext
from agent.models.enums import EventType, FeatureId
from agent.models.map import GameMap
from agent.models.position import Position
from agent.services.visibility_service import VisibilityService


def make_dash_action() -> DashAction:
    return DashAction(
        id="dash",
        name="Dash",
        description="Dash.",
        range=5,
    )


def test_dash(actor: Character, game_map: GameMap) -> None:
    initial_speed = actor.speed
    action = make_dash_action()

    target = Position(x=3, y=3)
    assert actor.pos != target

    action.execute(actor, target, ctx=CombatContext(map=game_map))

    assert actor.pos == target
    assert actor.current_speed == initial_speed

    action.finalize(actor)
    assert actor.action_economy.movement_available is False
    assert actor.action_economy.standard_actions == 0
    assert actor.current_speed < initial_speed
    assert actor.action_economy.movement_used > 0

    assert action.is_available(actor.action_economy) is False


def test_dash_doesnt_breaks_stealth(actor: Character, game_map: GameMap) -> None:
    VisibilityService.hide(actor)
    actor.passives.append(Trait(feature_id=FeatureId.STEALTH, source_id="hide", event_type=EventType.MODIFIER))
    action = make_dash_action()

    target = Position(x=3, y=3)
    action.execute(actor, target, ctx=CombatContext(map=game_map))
    action.finalize(actor)

    assert actor.is_hidden is True
    assert actor.stealth_value > 0
