from collections.abc import Iterator

import pytest
from textual.app import App
from textual.widgets import Static

from agent.character.character import Character
from agent.main import MAP_SIZE
from agent.models.map import GameMap
from agent.models.position import Position
from agent.models.state import State
from agent.ui.map_panel import InteractiveMapGrid, MapCell, MapPanel


class TestApp(App):
    """Test application for MapPanel."""

    def compose(self) -> Iterator[MapPanel]:
        yield MapPanel()


@pytest.fixture
def app() -> App:
    return TestApp()


@pytest.mark.asyncio
async def test_visibility(app: App, actor: Character, target: Character) -> None:
    actor.pos = Position(x=1, y=1, direction="SE")
    target.pos = Position(x=5, y=5, direction="N")

    map_str = [
        "############",
        "#..........#",
        "#...###....#",
        "#...###....#",
        "#..........#",
        "#..........#",
        "#..#..##...#",
        "#####.######",
    ]
    walls = [Position(x=x, y=y) for y, row in enumerate(map_str) for x, ch in enumerate(row) if ch == "#"]
    game_map = GameMap(
        map="",
        width=MAP_SIZE[0],
        height=MAP_SIZE[1],
        walls=walls,
        characters={actor.id: actor.pos, target.id: target.pos},
        icons={actor.id: actor.icon, target.id: target.icon},
    )

    state = State(
        map=game_map,
        characters={c.id: c for c in [actor, target]},
        parties={actor.party.id: actor.party, target.party.id: target.party},
        turn_order=[c.id for c in [actor, target]],
    )

    state.update_visibility(actor=actor)
    assert state.visibility[actor.id] == [target.id]

    async with app.run_test() as pilot:
        panel = app.query_one(MapPanel)
        panel.update_state(state)
        await pilot.pause()

        grid = panel.query_one(InteractiveMapGrid)

        # Click on target's cell
        grid.post_message(MapCell.Clicked(x=target.pos.x, y=target.pos.y))
        await pilot.pause()

        # Check the info text
        info_widget = app.query_one("#map-info", Static)
        info_text = str(info_widget.content)

        # Verify the info contains expected information about target
        assert f"Position: ({target.pos.x}, {target.pos.y})" in info_text
        assert f"Facing {target.pos.direction}" in info_text
        assert f"Character: {target.name}" in info_text
        assert f"HP: {target.attributes.hp}/{target.max_hp}" in info_text
        assert "Out of sight" not in info_text

        # Check that vision cone is displayed (cells should have "in-vision" class)
        visible_positions = game_map.get_visible_positions(target)
        visible_positions.remove(target.pos)  # Exclude target's position

        for pos in visible_positions:
            cell = grid.cells[pos.y][pos.x]
            assert cell.has_class("in-vision"), f"Cell at ({pos.x}, {pos.y}) should be in vision cone"
