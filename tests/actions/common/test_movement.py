from agent.actions.common.move import MovementAction
from agent.character.character import Character
from agent.models.context import CombatContext
from agent.models.map import GameMap
from agent.models.position import Position


def make_movement_action() -> MovementAction:
    return MovementAction(
        id="move",
        name="Move",
        description="Movement.",
        range=5,
    )


def test_movement(actor: Character, game_map: GameMap) -> None:
    initial_speed = actor.speed
    action = make_movement_action()

    target = Position(x=3, y=3)
    assert actor.pos != target

    action.execute(actor, target, ctx=CombatContext(map=game_map))

    assert actor.pos == target
    assert actor.current_speed == initial_speed

    action.finalize(actor)
    assert actor.action_economy.movement_available is False
    assert actor.current_speed < initial_speed
    assert actor.action_economy.movement_used > 0
    assert action.is_available(actor.action_economy) is False
