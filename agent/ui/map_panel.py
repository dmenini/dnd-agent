from textual.app import ComposeResult
from textual.containers import Grid, ScrollableContainer
from textual.message import Message
from textual.widgets import Static

from agent.models.map import EMPTY_CELL, WALL_CELL, GameMap
from agent.models.state import State


class MapCell(Static):
    """A single cell in the map grid."""

    class Clicked(Message):
        """Posted when a cell is clicked."""

        def __init__(
            self,
            x: int,
            y: int,
            info: str,
        ) -> None:
            super().__init__()
            self.x = x
            self.y = y
            self.info = info

    def __init__(self, x: int, y: int, content: str = " ", info: str = "", classes: str | None = None) -> None:
        super().__init__(content=content, classes=classes)
        self.x = x
        self.y = y
        self.info = info
        self.content = content
        self.tooltip = f"({x}, {y})"
        self.update(content)

    def on_click(self) -> None:
        """Handle click event."""
        # Deselect all other cells
        for cell in self.app.query(MapCell):
            cell.remove_class("selected")

        # Select this cell
        self.add_class("selected")

        self.post_message(self.Clicked(self.x, self.y, self.info))


class InteractiveMapGrid(Grid):
    """An interactive grid display for the game map."""

    DEFAULT_CSS = """
    InteractiveMapGrid {
        content-align: center middle;
        padding: 0;
        margin: 0;
        grid-gutter: 0;
    }

    MapCell {
        width: 4;
        height: 2;
        padding: 0;
        margin: 0;
        content-align: center middle;
    }

    MapCell.light {
        background: $surface-darken-1;
    }

    MapCell.dark {
        background: $surface-darken-3;
    }

    MapCell:hover {
        background: $boost;
    }

    MapCell.selected {
        background: $accent;
        text-style: bold;
    }
    """

    def __init__(self, game_map: GameMap, state: State) -> None:
        super().__init__()
        self.game_map = game_map
        self.grid = game_map.grid
        self.state = state
        self.cells: list[list[MapCell]] = []

    def on_mount(self) -> None:
        """Set up grid layout cleanly."""
        if not self.game_map:
            return
        self.styles.grid_size_columns = self.game_map.width
        self.styles.grid_size_rows = self.game_map.height

        # Set explicit size to ensure scrolling
        self.styles.width = self.game_map.width * 4  # 3 columns per cell
        self.styles.height = self.game_map.height * 2  # 2 rows per cell

    def compose(self) -> ComposeResult:
        """Create the grid of cells."""
        for y in range(self.game_map.height):
            row = []
            for x in range(self.game_map.width):
                cell_content = self._get_cell_content(x, y)
                info = self._get_cell_info(x, y)
                color_class = "light" if (x + y) % 2 == 0 else "dark"
                cell = MapCell(x=x, y=y, content=cell_content, info=info, classes=color_class)
                row.append(cell)
                yield cell
            self.cells.append(row)

    def _get_cell_content(self, x: int, y: int) -> str:
        content = self.grid[y][x]
        if content == EMPTY_CELL:
            return ""
        return content.strip()

    def _get_cell_info(self, x: int, y: int) -> str:
        """Generate information for a cell."""
        lines = [f"Position: ({x}, {y})"]

        # Check if there's a character at this position
        for cid, char in self.state.characters.items():
            if char.pos.x == x and char.pos.y == y:
                lines.append(f"Character: {char.name}")
                lines.append(f"HP: {char.attributes.hp}/{char.max_hp}")
                if cid not in self.state.visible_characters:
                    lines.append("Out of sight")
                if self.state.turn_order:
                    dist = self.state.map.distance(self.state.current_actor.pos, char.pos)
                    lines.append(f"Distance: {dist}m")
                break

        return " | ".join(lines)

    def on_map_cell_clicked(self, message: MapCell.Clicked) -> None:
        """Handle cell click events."""
        # Post a message to parent or handle directly
        self.app.query_one("#map-detail", Static).update(message.info)


class MapPanel(Static):
    """Display map panel."""

    DEFAULT_CSS = """
    #map-display-area {
        height: 90%;
        align: center middle;
        padding: 1 0 1 2;
    }

    #map-detail {
        height: 10%;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        """Build static structure of the panel."""
        with ScrollableContainer(id="map-display-area"):
            yield Static("Loading map...", id="map-content")
        yield Static("Click over cells for info", id="map-detail")

    def update_state(self, state: State) -> None:
        """Update the map display according to the current state."""
        map_content_container = self.query_one("#map-display-area", ScrollableContainer)

        if not state.map:
            # Remove old grid and show empty message
            map_content_container.remove_children()
            map_content_container.mount(Static("No map data available"))
            return

        # Remove old grid and create new one
        map_content_container.remove_children()
        interactive_grid = InteractiveMapGrid(state.map, state)
        map_content_container.mount(interactive_grid)
