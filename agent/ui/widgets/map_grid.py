from typing import Literal

from textual import events
from textual.app import ComposeResult
from textual.containers import Grid
from textual.message import Message
from textual.widgets import Static

from agent.models.map import EMPTY_CELL, WALL_CELL
from agent.models.position import Position
from agent.models.state import State

DEFAULT_INFO = "Select a cell to see info"


class MapCell(Static):
    """A single cell in the map grid."""

    DEFAULT_CSS = """
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
        opacity: 0.9;
    }

    MapCell.wall {
        background: $primary-darken-3;
        text-style: bold;
    }
    """

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

    def is_wall(self) -> bool:
        return self.has_class("wall")

    def is_selected(self) -> bool:
        return self.has_class("selected")

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
    """

    BINDINGS = [
        ("up", "move_up", "Move Up"),
        ("down", "move_down", "Move Down"),
        ("left", "move_left", "Move Left"),
        ("right", "move_right", "Move Right"),
    ]

    def __init__(self, state: State, cell_size: Literal["small", "large"] = "large") -> None:
        super().__init__()

        if state.map is None:
            msg = "Map must be defined"
            raise ValueError(msg)

        self.game_map = state.map
        self.grid = state.map.grid
        self.state = state
        self.cells: list[list[MapCell]] = []
        self.selected_x: int | None = 0
        self.selected_y: int | None = 0
        self.can_focus = True  # Allow grid to receive keyboard events
        self.cell_size = cell_size

    def on_mount(self) -> None:
        """Set up grid layout cleanly."""
        if not self.game_map:
            return
        self.styles.grid_size_columns = self.game_map.width
        self.styles.grid_size_rows = self.game_map.height

        # Set explicit size to ensure scrolling and square cells
        if self.cell_size == "large":
            self.styles.width = self.game_map.width * 4
            self.styles.height = self.game_map.height * 2
        else:
            self.styles.width = self.game_map.width * 2
            self.styles.height = self.game_map.height * 1

    def compose(self) -> ComposeResult:
        """Create the grid of cells."""
        for y in range(self.game_map.height):
            row = []
            for x in range(self.game_map.width):
                cell_content = self._get_cell_content(x, y)
                color_class = "light" if (x + y) % 2 == 0 else "dark"

                if Position(x=x, y=y) in self.game_map.walls:
                    color_class = "wall"

                cell = MapCell(x=x, y=y, content=cell_content, classes=color_class)
                row.append(cell)
                yield cell
            self.cells.append(row)

        if self.state.current_actor:
            pos = self.state.current_actor.combat.pos
            self._select_cell(pos.x, pos.y)

    def _get_cell_content(self, x: int, y: int) -> str:
        content = self.grid[y][x]
        if content in {EMPTY_CELL, WALL_CELL}:
            return ""
        return content.strip()

    def _get_cell_info(self, x: int, y: int) -> str:
        """Generate detailed information for a cell."""
        lines = [f"Position: ({x}, {y})"]

        pos = Position(x=x, y=y)

        if pos in self.game_map.walls:
            lines.append("Wall")

        # Check if there's a character at this position
        for cid, char in self.state.characters.items():
            if char.pos == pos:
                lines.append(f"Facing {char.pos.direction}")
                lines.append(f"Character: {char.name}")
                lines.append(f"HP: {char.attributes.hp}/{char.max_hp}")
                if (actor := self.state.current_actor) and actor.id != cid:
                    dist = self.game_map.distance(actor.combat.pos, char.combat.pos)
                    lines.append(f"Distance: {dist}m")
                    if cid not in self.state.visibility[actor.id]:
                        lines.append("Out of sight")
                break

        return " | ".join(lines)

    def on_key(self, event: events.Key) -> None:
        """Handle keyboard navigation."""
        key = event.key

        sel_x, sel_y = self.selected_x or 0, self.selected_y or 0

        if key == "up":
            self._select_cell(sel_x, sel_y - 1)
            event.prevent_default()
        elif key == "down":
            self._select_cell(sel_x, sel_y + 1)
            event.prevent_default()
        elif key == "left":
            self._select_cell(sel_x - 1, sel_y)
            event.prevent_default()
        elif key == "right":
            self._select_cell(sel_x + 1, sel_y)
            event.prevent_default()

    def on_map_cell_clicked(self, message: MapCell.Clicked) -> None:
        """Handle cell click events."""
        x, y = message.x, message.y

        if x is None or y is None:
            return

        # Do not select walls
        if self.cells[y][x].is_wall():
            return

        # If clicking the same cell again → unselect
        if self.selected_x == x and self.selected_y == y:
            self._unselect_cell()
        else:
            self._select_cell(x, y)

    def _select_cell(self, x: int, y: int) -> None:
        """Select a cell and show its information."""
        # First, clear previous selection and vision cone
        for row in self.cells:
            for cell in row:
                cell.remove_class("selected")
                cell.remove_class("in-vision")

        # Check bounds
        if not (0 <= x < self.game_map.width and 0 <= y < self.game_map.height):
            return

        self.selected_x = x
        self.selected_y = y
        selected_cell = self.cells[y][x]
        selected_cell.add_class("selected")

        # Show cell info
        info = self._get_cell_info(x, y)
        self.app.query_one("#map-info", Static).update(info)

        # Show vision cone if there's a character at this position
        self._show_vision_cone(x, y)

    def _unselect_cell(self) -> None:
        """Clear current selection and vision cone."""
        for row in self.cells:
            for cell in row:
                cell.remove_class("selected")
                cell.remove_class("in-vision")

        self.selected_x = None
        self.selected_y = None

        # Clear info panel
        self.app.query_one("#map-info", Static).update(DEFAULT_INFO)

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

        # Exclude character position
        visible = self.game_map.get_visible_positions(character)
        visible.remove(character.pos)

        for pos in visible:
            self.cells[pos.y][pos.x].add_class("in-vision")
