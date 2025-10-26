from agent.actions.common.hide import HideAction
from agent.character.character import Character
from agent.models.context import CombatContext
from agent.models.map import GameMap
from agent.models.position import Position


def test_hide_success(actor: Character, target: Character, game_map: GameMap) -> None:
    action = HideAction()

    target.pos = Position(x=5, y=5)
    actor.pos = Position(x=1, y=1)
    game_map.walls = [Position(x=2, y=2), Position(x=3, y=3)]  # block los
    game_map.characters = {actor.id: actor.pos, target.id: target.pos}

    action.execute(actor, None, ctx=CombatContext(map=game_map, enemies=[target]))

    assert actor.is_hidden is True
    assert actor.stealth_value > 0

    action.finalize(actor)
    assert actor.action_economy.standard_actions == 0
    assert action.is_available(actor.action_economy) is False


def test_hide_failure(actor: Character, target: Character, game_map: GameMap) -> None:
    action = HideAction()

    actor.pos = Position(x=1, y=1)
    target.pos = Position(x=5, y=5, direction="SW")
    game_map.characters = {actor.id: actor.pos, target.id: target.pos}

    action.execute(actor, None, ctx=CombatContext(map=game_map, enemies=[target]))

    assert actor.is_hidden is False
    assert actor.stealth_value == 0

    action.finalize(actor)
    assert actor.action_economy.standard_actions == 0
    assert action.is_available(actor.action_economy) is False
