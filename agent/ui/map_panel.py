from textual import events
from textual.app import ComposeResult
from textual.containers import Grid, ScrollableContainer
from textual.message import Message
from textual.widgets import Static

from agent.models.map import EMPTY_CELL, GameMap
from agent.models.position import Position
from agent.models.state import State


class MapCell(Static):
    """A single cell in the map grid."""

    class Clicked(Message):
        """Posted when a cell is clicked."""

        def __init__(self, x: int, y: int) -> None:
            super().__init__()
            self.x = x
            self.y = y

    def __init__(self, x: int, y: int, content: str = " ", classes: str | None = None) -> None:
        super().__init__(content=content, classes=classes)
        self.x = x
        self.y = y
        self.tooltip = f"({x}, {y})"  # Simple tooltip with coordinates
        self.update(content)

    def on_click(self) -> None:
        """Handle click event."""
        self.post_message(self.Clicked(self.x, self.y))


class InteractiveMapGrid(Grid):
    """An interactive grid display for the game map."""

    DEFAULT_CSS = """
    InteractiveMapGrid {
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

    MapCell.in-vision {
        background: $warning-darken-1;
        opacity: 0.7;
    }
    """

    def __init__(self, game_map: GameMap, state: State) -> None:
        super().__init__()
        self.game_map = game_map
        self.grid = game_map.grid
        self.state = state
        self.cells: list[list[MapCell]] = []
        self.selected_x: int = 0
        self.selected_y: int = 0
        self.can_focus = True  # Allow grid to receive keyboard events

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
                color_class = "light" if (x + y) % 2 == 0 else "dark"
                cell = MapCell(x=x, y=y, content=cell_content, classes=color_class)
                row.append(cell)
                yield cell
            self.cells.append(row)

    def _get_cell_content(self, x: int, y: int) -> str:
        content = self.grid[y][x]
        if content == EMPTY_CELL:
            return ""
        return content.strip()

    def _get_cell_info(self, x: int, y: int) -> str:
        """Generate detailed information for a cell."""
        lines = [f"Position: ({x}, {y})"]

        # Check if there's a character at this position
        for cid, char in self.state.characters.items():
            if char.pos.x == x and char.pos.y == y:
                lines.append(f"Character: {char.name}")
                lines.append(f"HP: {char.attributes.hp}/{char.max_hp}")
                if self.state.turn_order:
                    if cid not in self.state.visible_characters:
                        lines.append("Out of sight")
                    dist = self.state.map.distance(self.state.current_actor.pos, char.pos)
                    lines.append(f"Distance: {dist}m")
                break

        return " | ".join(lines)

    def _select_cell(self, x: int, y: int) -> None:
        """Select a cell and show its information."""
        # Deselect all cells and clear vision cone
        for row in self.cells:
            for cell in row:
                cell.remove_class("selected")
                cell.remove_class("in-vision")

        # Select new cell
        if 0 <= x < self.game_map.width and 0 <= y < self.game_map.height:
            self.selected_x = x
            self.selected_y = y
            self.cells[y][x].add_class("selected")

            # Show cell info
            info = self._get_cell_info(x, y)
            self.app.query_one("#map-info", Static).update(info)

            # Show vision cone if there's a character at this position
            self._show_vision_cone(x, y)

    def _show_vision_cone(self, x: int, y: int) -> None:
        """Highlight cells in the vision cone of a character at given position."""
        # Find character at this position
        character = None
        for char in self.state.characters.values():
            if char.pos.x == x and char.pos.y == y:
                character = char
                break

        if not character:
            return

        for tx in range(self.game_map.width):
            for ty in range(self.game_map.height):
                if self.game_map.within_visibility_range(character, target=Position(x=tx, y=ty)):
                    self.cells[ty][tx].add_class("in-vision")

    def on_key(self, event: events.Key) -> None:
        """Handle keyboard navigation."""
        key = event.key

        if key == "up":
            self._select_cell(self.selected_x, self.selected_y - 1)
            event.prevent_default()
        elif key == "down":
            self._select_cell(self.selected_x, self.selected_y + 1)
            event.prevent_default()
        elif key == "left":
            self._select_cell(self.selected_x - 1, self.selected_y)
            event.prevent_default()
        elif key == "right":
            self._select_cell(self.selected_x + 1, self.selected_y)
            event.prevent_default()

    def on_map_cell_clicked(self, message: MapCell.Clicked) -> None:
        """Handle cell click events."""
        self._select_cell(message.x, message.y)


class MapPanel(Static):
    """Display map panel."""

    DEFAULT_CSS = """
    #map-display-area {
        height: 90%;
        align: center middle;
        padding: 1 0 1 2;
    }

    #map-info {
        height: 10%;
        text-align: center;
        background: $surface;
    }
    """

    def compose(self) -> ComposeResult:
        """Build static structure of the panel."""
        with ScrollableContainer(id="map-display-area"):
            yield Static("Loading map...", id="map-content")
        yield Static("Select a cell to see info", id="map-info")

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
