import pytest

from agent.actions.base import Action, ActionCategory, ActionType
from agent.character.character import Character
from agent.models.decision import DecisionResult
from agent.models.enums import TargetingType
from agent.models.map import GameMap
from agent.models.position import Position


@pytest.fixture
def base_decision() -> DecisionResult:
    return DecisionResult(
        action_id="attack_1",
        target_hits={"enemy1": 1},
        target_position=None,
        description="",
    )


@pytest.fixture
def action() -> Action:
    return Action(
        id="attack_1",
        name="",
        description="",
        hits=1,
        targeting=TargetingType.SINGLE,
        action_type=ActionType.ATTACK,
        category=ActionCategory.STANDARD,
    )


def test_validate_self_targeting_valid_self_target(base_decision: DecisionResult) -> None:
    ok, msg = base_decision.validate_self_targeting("enemy1")
    assert ok is True
    assert msg == ""


def test_validate_self_targeting_invalid_other_target(base_decision: DecisionResult) -> None:
    ok, msg = base_decision.validate_self_targeting("other-actor")
    assert ok is False
    assert "targets SELF only" in msg


def test_validate_self_targeting_no_targets(base_decision: DecisionResult) -> None:
    base_decision.target_hits = {}
    ok, msg = base_decision.validate_self_targeting("actor1")
    assert ok is True
    assert msg == ""


def test_validate_area_targeting_missing_position(base_decision: DecisionResult) -> None:
    base_decision.target_position = None
    ok, msg = base_decision.validate_area_targeting()
    assert ok is False
    assert "requires a target position" in msg


def test_validate_area_targeting_with_targets(base_decision: DecisionResult) -> None:
    base_decision.target_position = Position(x=1, y=1)
    base_decision.target_hits = {"enemy1": 1}
    ok, msg = base_decision.validate_area_targeting()
    assert ok is False
    assert "targets an area, not specific entities" in msg


def test_validate_area_targeting_valid(base_decision: DecisionResult) -> None:
    base_decision.target_position = Position(x=2, y=2)
    base_decision.target_hits = {}
    ok, msg = base_decision.validate_area_targeting()
    assert ok is True
    assert msg == ""


def test_validate_single_targeting_no_targets(base_decision: DecisionResult, action: Action) -> None:
    base_decision.target_hits = {}
    ok, msg = base_decision.validate_single_targeting(action)
    assert ok is False
    assert "requires at least one valid target ID" in msg


def test_validate_single_targeting_too_many_targets(base_decision: DecisionResult, action: Action) -> None:
    base_decision.target_hits = {"enemy1": 1, "enemy2": 1}
    ok, msg = base_decision.validate_single_targeting(action)
    assert ok is False
    assert "targets only one enemy" in msg


def test_validate_single_targeting_too_many_hits(base_decision: DecisionResult, action: Action) -> None:
    base_decision.target_hits = {"enemy1": 3}
    ok, msg = base_decision.validate_single_targeting(action)
    assert ok is False
    assert "allows up to" in msg


def test_validate_single_targeting_valid(base_decision: DecisionResult, action: Action) -> None:
    base_decision.target_hits = {"enemy1": 2}
    action.hits = 2
    ok, msg = base_decision.validate_single_targeting(action)
    assert ok is True
    assert msg == ""


def test_validate_multi_targeting_single_target(base_decision: DecisionResult, action: Action) -> None:
    base_decision.target_hits = {"enemy1": 1}
    action.targeting = TargetingType.MULTI
    ok, msg = base_decision.validate_multi_targeting(action)
    assert ok is True
    assert msg == ""


def test_validate_multi_targeting_too_many_hits(base_decision: DecisionResult, action: Action) -> None:
    base_decision.target_hits = {"enemy1": 3, "enemy2": 2}
    action.targeting = TargetingType.MULTI
    action.hits = 3
    ok, msg = base_decision.validate_multi_targeting(action)
    assert ok is False
    assert "at most" in msg


def test_validate_multi_targeting_valid(base_decision: DecisionResult, action: Action) -> None:
    base_decision.target_hits = {"enemy1": 2, "enemy2": 1}
    action.hits = 3
    ok, msg = base_decision.validate_multi_targeting(action)
    assert ok is True
    assert msg == ""


def test_validate_targets_exist_valid(base_decision: DecisionResult, action: Action, actor: Character) -> None:
    base_decision.target_hits = {actor.id: 1}
    ok, msg = base_decision.validate_targets_exist(characters={actor.id: actor})
    assert ok is True
    assert msg == ""


def test_validate_targets_exist_missing_chars(base_decision: DecisionResult, action: Action, actor: Character) -> None:
    base_decision.target_hits = {"enemy1": 1}
    ok, msg = base_decision.validate_targets_exist(characters={actor.id: actor})
    assert ok is False
    assert "not found" in msg


def test_validate_targets_alive_valid(base_decision: DecisionResult, action: Action, actor: Character) -> None:
    base_decision.target_hits = {actor.id: 1}
    ok, msg = base_decision.validate_targets_alive(characters={actor.id: actor})
    assert ok is True
    assert msg == ""


def test_validate_targets_not_alive(base_decision: DecisionResult, action: Action, actor: Character) -> None:
    base_decision.target_hits = {actor.id: 1}
    actor.attributes.hp = 0
    ok, msg = base_decision.validate_targets_alive(characters={actor.id: actor})
    assert ok is False
    assert "already down" in msg


def test_validate_friendly_fire_valid(
    base_decision: DecisionResult, action: Action, actor: Character, target: Character
) -> None:
    base_decision.target_hits = {target.id: 1}
    ok, msg = base_decision.validate_friendly_fire(actor, characters={actor.id: actor, target.id: target})
    assert ok is True
    assert msg == ""


def test_validate_friendly_fire_on_ally(base_decision: DecisionResult, action: Action, actor: Character) -> None:
    base_decision.target_hits = {actor.id: 1}
    ok, msg = base_decision.validate_friendly_fire(actor, characters={actor.id: actor})
    assert ok is False
    assert "cannot attack ally" in msg


def test_validate_range_valid(
    base_decision: DecisionResult, action: Action, actor: Character, target: Character
) -> None:
    base_decision.target_hits = {target.id: 1}
    ok, msg = base_decision.validate_range(
        actor, characters={actor.id: actor, target.id: target}, available_movement=100
    )
    assert ok is True
    assert msg == ""


def test_validate_range_too_far(
    base_decision: DecisionResult, action: Action, actor: Character, target: Character
) -> None:
    base_decision.target_hits = {target.id: 1}
    ok, msg = base_decision.validate_range(actor, characters={actor.id: actor, target.id: target}, available_movement=0)
    assert ok is False
    assert "out of range" in msg


def test_validate_movement_valid(
    base_decision: DecisionResult, action: Action, actor: Character, game_map: GameMap
) -> None:
    base_decision.target_position = Position(x=2, y=2)
    game_map.characters = {actor.id: Position(x=0, y=0)}
    ok, msg = base_decision.validate_movement(actor, action, game_map=game_map)
    assert ok is True
    assert msg == ""


def test_validate_movement_outbound(
    base_decision: DecisionResult, action: Action, actor: Character, target: Character, game_map: GameMap
) -> None:
    base_decision.target_position = Position(x=10, y=8)
    game_map.characters = {actor.id: Position(x=0, y=0)}
    ok, msg = base_decision.validate_movement(actor, action, game_map=game_map)
    assert ok is False
    assert "out of map bounds" in msg


def test_validate_movement_too_far(
    base_decision: DecisionResult, action: Action, actor: Character, target: Character, game_map: GameMap
) -> None:
    base_decision.target_position = Position(x=9, y=9)
    game_map.characters = {actor.id: Position(x=0, y=0)}
    actor.action_economy.movement_used = 10
    ok, msg = base_decision.validate_movement(actor, action, game_map=game_map)
    assert ok is False
    assert "too far" in msg


def test_validate_movement_taken(
    base_decision: DecisionResult, action: Action, actor: Character, target: Character, game_map: GameMap
) -> None:
    action.range = 10
    game_map.characters = {actor.id: Position(x=0, y=0)}
    base_decision.target_position = Position(x=0, y=0)
    ok, msg = base_decision.validate_movement(actor, action, game_map=game_map)
    assert ok is False
    assert "already occupied" in msg
