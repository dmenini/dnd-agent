from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Static

from agent.models.state import State
from agent.ui.widgets.map_grid import DEFAULT_INFO, InteractiveMapGrid


class MapPanel(Static):
    """Display map panel."""

    DEFAULT_CSS = """
    #map-display-area {
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
            yield Static("Loading map...", id="map-content")
        yield Static(DEFAULT_INFO, id="map-info")

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
        interactive_grid = InteractiveMapGrid(state)
        map_content_container.mount(interactive_grid)
