from textual.app import ComposeResult
from textual.containers import Container, Grid, VerticalScroll
from textual.css.model import RuleSet
from textual.message import Message
from textual.widgets import Rule, Static

from agent.models.map import EMPTY_CELL, GameMap, WALL_CELL
from agent.models.state import State


class MapCell(Static):
    """A single cell in the map grid."""

    class Clicked(Message):
        """Posted when a cell is clicked."""

        def __init__(self, x: int, y: int, info: str, ) -> None:
            super().__init__()
            self.x = x
            self.y = y
            self.info = info

    def __init__(self, x: int, y: int, content: str = " ", tooltip_info: str = "", classes: str | None = None) -> None:
        super().__init__(content=content, classes=classes)
        self.x = x
        self.y = y
        self.content = content
        self.tooltip_info = tooltip_info
        self.update(content)

    def on_click(self) -> None:
        """Handle click event."""
        # Deselect all other cells
        for cell in self.app.query(MapCell):
            cell.remove_class("selected")

        # Select this cell
        self.add_class("selected")

        self.post_message(self.Clicked(self.x, self.y, self.tooltip_info))

    def on_enter(self) -> None:
        """Handle mouse enter."""
        if self.tooltip_info:
            # Update a tooltip widget or status bar
            self.app.query_one("#map-tooltip", Static).update(self.tooltip_info)


class InteractiveMapGrid(Grid):
    """An interactive grid display for the game map."""

    DEFAULT_CSS = """
    InteractiveMapGrid {
        align: center middle;
        padding: 0;
        margin: 0;
        grid-gutter: 0;
        width: 90w;
        height: 90h;
    }

    MapCell {
        width: 1fr;
        height: 1fr;
        padding: 0;
        margin: 0;
        border: none;
        content-align: center middle;
    }

    MapCell.light {
        background: $surface;
    }
    
    MapCell.dark {
        background: $surface-darken-1;
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

    def compose(self) -> ComposeResult:
        """Create the grid of cells."""
        for y in range(self.game_map.height):
            row = []
            for x in range(self.game_map.width):
                cell_content = self._get_cell_content(x, y)
                tooltip = self._get_tooltip_info(x, y)
                color_class = "light" if (x + y) % 2 == 0 else "dark"
                cell = MapCell(x=x, y=y, content=cell_content, tooltip_info=tooltip, classes=color_class)
                row.append(cell)
                yield cell
            self.cells.append(row)

    def _get_cell_content(self, x: int, y: int) -> str:
        return self.grid[y][x].strip()

    def _get_tooltip_info(self, x: int, y: int) -> str:
        """Generate tooltip information for a cell."""
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

        # Add tile type information
        cell_content = self._get_cell_content(x, y)
        if cell_content == WALL_CELL:
            lines.append("Type: Wall")
        elif cell_content == EMPTY_CELL:
            lines.append("Type: Walkable")

        return " | ".join(lines)

    def on_map_cell_clicked(self, message: MapCell.Clicked) -> None:
        """Handle cell click events."""
        # Post a message to parent or handle directly
        self.app.query_one("#map-tooltip", Static).update(message.info)
        self.app.notify(f"Clicked cell at ({message.x}, {message.y})")


class MapPanel(Static):
    """Display map panel."""

    DEFAULT_CSS = """
    #map-display-area {
        height: 90%;
        align: center middle;
        padding: 0;
    }

    #map-tooltip {
        height: 10%;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        """Build static structure of the panel."""
        with VerticalScroll(id="map-container"):
            with Container(id="map-display-area"):
                yield Static("Loading map...", id="map-content")
            yield Static("Hover over cells for info", id="map-tooltip")

    def update_state(self, state: State) -> None:
        """Update the map display according to the current state."""
        map_content_container = self.query_one("#map-display-area", Container)

        if not state.map:
            # Remove old grid and show empty message
            map_content_container.remove_children()
            map_content_container.mount(Static("No map data available"))
            return

        # Remove old grid and create new one
        map_content_container.remove_children()
        interactive_grid = InteractiveMapGrid(state.map, state)
        map_content_container.mount(interactive_grid)
