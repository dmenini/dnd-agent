from textual.widgets import Static

from agent.models.state import State


class MapPanel(Static):
    """Top-left: the map."""

    def update_state(self, state: State) -> None:
        if state.map:
            self.update(str(state.map))
