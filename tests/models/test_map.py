import pytest

from agent.character.character import Character
from agent.models.map import GameMap, is_inbound
from agent.models.position import Direction, Position


def test_validate_not_overlapping_success() -> None:
    characters = {
        "a": Position(x=0, y=0),
        "b": Position(x=1, y=1),
        "c": Position(x=2, y=2),
    }
    game_map = GameMap(width=5, height=5, characters=characters, walls=[], map="")
    assert game_map.characters["a"] == Position(x=0, y=0)
    assert game_map.characters["b"] == Position(x=1, y=1)
    assert game_map.characters["c"] == Position(x=2, y=2)


def test_validate_not_overlapping_failure() -> None:
    characters = {
        "a": Position(x=0, y=0),
        "b": Position(x=0, y=0),  # overlap
    }
    with pytest.raises(ValueError, match="Some characters share the same coordinates"):
        GameMap(width=5, height=5, characters=characters, walls=[], map="")


def test_validate_inbound_success_removes_outbound_walls() -> None:
    characters = {
        "a": Position(x=0, y=0),
        "b": Position(x=4, y=4),
    }
    walls = [
        Position(x=1, y=1),  # inside
        Position(x=6, y=0),  # outside
        Position(x=-1, y=2),  # outside
    ]
    game_map = GameMap(width=5, height=5, characters=characters, walls=walls, map="")

    # Check characters remain unchanged
    assert game_map.characters["a"] == Position(x=0, y=0)
    assert game_map.characters["b"] == Position(x=4, y=4)

    # Check walls outside bounds removed
    assert all(is_inbound(w, width=5, height=5) for w in game_map.walls)
    assert len(game_map.walls) == 1
    assert game_map.walls[0] == Position(x=1, y=1)


def test_validate_inbound_failure_character_out_of_bounds() -> None:
    characters = {
        "a": Position(x=0, y=0),
        "b": Position(x=5, y=2),  # x out of bounds
    }
    with pytest.raises(ValueError, match="Character b position"):
        GameMap(width=5, height=5, characters=characters, walls=[], map="")


def test_validate_inbound_edge_case_character_at_bounds() -> None:
    characters = {
        "a": Position(x=0, y=0),
        "b": Position(x=4, y=4),  # width-1, height-1
    }
    game_map = GameMap(width=5, height=5, characters=characters, walls=[], map="")

    # All positions valid
    assert game_map.characters["a"] == Position(x=0, y=0)
    assert game_map.characters["b"] == Position(x=4, y=4)


def test_visible_in_range_no_obstacles(game_map: GameMap, actor: Character, target: Character) -> None:
    actor.pos = Position(x=1, y=1, direction="E")
    target.pos = Position(x=3, y=1)
    game_map.characters = {actor.id: actor.pos, target.id: target.pos}

    assert game_map.within_visibility_range(actor, target.pos) is True


@pytest.mark.parametrize(
    ("pos1", "pos2"),
    [
        (Position(x=1, y=1, direction="E"), Position(x=3, y=1)),
        (Position(x=1, y=1, direction="S"), Position(x=1, y=2)),
        (Position(x=1, y=1, direction="W"), Position(x=0, y=1)),
        (Position(x=1, y=1, direction="N"), Position(x=1, y=0)),
        (Position(x=1, y=1, direction="SE"), Position(x=2, y=2)),
        (Position(x=1, y=1, direction="NW"), Position(x=0, y=0)),
        (Position(x=1, y=1, direction="SW"), Position(x=0, y=2)),
        (Position(x=1, y=1, direction="NE"), Position(x=2, y=0)),
    ],
)
def test_visible_in_range(
    game_map: GameMap, actor: Character, target: Character, pos1: Position, pos2: Position
) -> None:
    actor.pos = pos1
    target.pos = pos2
    game_map.characters = {actor.id: actor.pos, target.id: target.pos}

    assert game_map.within_visibility_range(actor, target.pos) is True


def test_not_visible_out_of_range(game_map: GameMap, actor: Character, target: Character) -> None:
    actor.pos = Position(x=0, y=0)
    target.pos = Position(x=4, y=4)
    game_map.characters = {actor.id: actor.pos, target.id: target.pos}
    actor.attributes.vision_range = lambda: 2  # short-sighted

    assert game_map.within_visibility_range(actor, target.pos) is False


def test_out_of_vision_cone(game_map: GameMap, actor: Character, target: Character) -> None:
    actor.pos = Position(x=1, y=1, direction="W")
    target.pos = Position(x=3, y=1)
    game_map.characters = {actor.id: Position(x=1, y=1), target.id: Position(x=3, y=1)}

    assert game_map.within_visibility_range(actor, target.pos) is False


def test_blocked_by_wall(game_map: GameMap, actor: Character, target: Character) -> None:
    actor.pos = Position(x=0, y=0)
    target.pos = Position(x=4, y=0)
    game_map.characters = {actor.id: actor.pos, target.id: target.pos}
    game_map.walls = [Position(x=2, y=0)]  # wall directly in line

    assert game_map.within_visibility_range(actor, target.pos) is False


def test_wall_not_on_path(game_map: GameMap, actor: Character, target: Character) -> None:
    actor.pos = Position(x=0, y=0, direction="E")
    target.pos = Position(x=4, y=0)
    game_map.characters = {actor.id: actor.pos, target.id: target.pos}
    game_map.walls = [Position(x=2, y=1)]  # wall near line, not blocking

    assert game_map.within_visibility_range(actor, target.pos) is True


def test_same_position_visible(game_map: GameMap, actor: Character, target: Character) -> None:
    actor.pos = Position(x=2, y=2)
    target.pos = Position(x=2, y=2)
    game_map.characters = {actor.id: actor.pos, target.id: target.pos}

    assert game_map.within_visibility_range(actor, target.pos) is True


def test_distance_same_position(game_map: GameMap) -> None:
    start = Position(x=1, y=1)
    end = Position(x=1, y=1)
    assert game_map.distance(start, end) == 0


def test_distance_straight_line(game_map: GameMap) -> None:
    start = Position(x=0, y=0)
    end = Position(x=0, y=3)
    assert game_map.distance(start, end) == 3


def test_distance_diagonal_requires_steps(game_map: GameMap) -> None:
    start = Position(x=0, y=0)
    end = Position(x=3, y=3)
    # BFS moves only orthogonally (up, down, left, right)
    # So the path is 6 steps (3 right + 3 up)
    assert game_map.distance(start, end) == 6


def test_distance_with_single_wall(game_map: GameMap) -> None:
    game_map.walls = [Position(x=1, y=0)]  # Block direct path
    start = Position(x=0, y=0)
    end = Position(x=2, y=0)

    # Must go around: (0,0)->(0,1)->(1,1)->(2,1)->(2,0) = 4 steps
    assert game_map.distance(start, end) == 4


def test_distance_with_multiple_walls(game_map: GameMap) -> None:
    game_map.walls = [
        Position(x=1, y=0),
        Position(x=1, y=1),
        Position(x=1, y=2),
    ]  # vertical wall
    start = Position(x=0, y=0)
    end = Position(x=2, y=0)

    # Must go around bottom edge: (0,0)->(0,1)->(0,2)->(0,3)->(1,3)->(2,3)->(2,2)->(2,1)->(2,0) = 8 steps
    assert game_map.distance(start, end) == 8


def test_unreachable_due_to_enclosed_target(game_map: GameMap) -> None:
    game_map.walls = [
        Position(x=1, y=0),
        Position(x=0, y=1),
        Position(x=1, y=1),
    ]
    start = Position(x=0, y=0)
    end = Position(x=1, y=1)

    # Target surrounded by walls and start
    assert game_map.distance(start, end) is None


def test_distance_out_of_bounds_returns_none(game_map: GameMap) -> None:
    start = Position(x=0, y=0)
    end = Position(x=10, y=10)  # Outside grid
    assert game_map.distance(start, end) is None


def test_visibility_no_walls(game_map: GameMap, actor: Character) -> None:
    """Test visible cells with 360 degree FoV."""

    actor.pos = Position(x=5, y=5)
    actor.attributes.base_vision_fov = 360
    actor.attributes.base_vision_range = 3

    visible = game_map.get_visible_positions(actor)

    # Rough check: should include a circle of radius 3 around the observer
    assert Position(x=5, y=5) in visible
    assert Position(x=8, y=5) in visible  # right
    assert Position(x=5, y=8) in visible  # down
    assert Position(x=2, y=5) in visible  # left
    assert Position(x=5, y=2) in visible  # up
    assert len(visible) > 20


def test_visibility_with_wall_blocking(game_map: GameMap, actor: Character) -> None:
    """Test with wall blocking visibility to the right."""
    walls = [Position(x=6, y=5)]
    game_map.walls = walls

    actor.pos = Position(x=5, y=5)
    actor.attributes.base_vision_fov = 360
    actor.attributes.base_vision_range = 3

    visible = game_map.get_visible_positions(actor)

    assert Position(x=5, y=5) in visible
    assert Position(x=6, y=5) in visible  # wall itself visible
    assert Position(x=7, y=5) not in visible  # blocked behind wall


@pytest.mark.parametrize(
    ("facing", "expected_visible"),
    [
        ("E", {Position(x=6, y=5)}),
        ("N", {Position(x=5, y=4)}),
        ("W", {Position(x=4, y=5)}),
        ("S", {Position(x=5, y=6)}),
    ],
)
def test_fov_directional(
    facing: Direction, expected_visible: set[Position], game_map: GameMap, actor: Character
) -> None:
    """Test visible cells with directional FoV."""
    actor.pos = Position(x=5, y=5, direction=facing)
    actor.attributes.base_vision_fov = 90
    actor.attributes.base_vision_range = 3

    visible = game_map.get_visible_positions(actor)

    # Ensure FOV is directional: cell in front is visible, cell behind is not
    for ex in expected_visible:
        assert ex in visible

    behind = Position(x=int(actor.pos.x - actor.pos.facing_vector[0]), y=int(actor.pos.y - actor.pos.facing_vector[1]))
    assert behind not in visible


def test_visibility_edges_of_map(game_map: GameMap, actor: Character) -> None:
    actor.pos = Position(x=0, y=0)
    actor.attributes.base_vision_fov = 90
    actor.attributes.base_vision_range = 3

    visible = game_map.get_visible_positions(actor)
    # Should not include out-of-bounds positions
    assert all(0 <= pos.x < game_map.width and 0 <= pos.y < game_map.height for pos in visible)
