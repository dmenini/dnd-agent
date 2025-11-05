from textual.app import ComposeResult
from textual.containers import Center, ScrollableContainer
from textual.widgets import Static

from agent.models.state import State
from agent.ui.widgets.map_grid import DEFAULT_INFO, InteractiveMapGrid


class MapPanel(Static):
    """Display map panel."""

    DEFAULT_CSS = """
    #map-display-area {
        text-align: center;
        align: center middle;
        margin: 1 0;
    }

    #map-info {
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        """Build static structure of the panel."""
        with ScrollableContainer(id="map-display-area"):
            yield Static("No map available", id="map-content")
        yield Static("", id="map-info")

    def update_state(self, state: State) -> None:
        """Update the map display according to the current state."""
        if not state.map:
            return

        map_content_container = self.query_one("#map-display-area", ScrollableContainer)
        map_content_container.remove_children()
        interactive_grid = InteractiveMapGrid(state)
        map_content_container.mount(interactive_grid)
