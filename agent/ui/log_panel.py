from rich.console import Group
from textual.widgets import Static

from agent.models.state import State


class LogPanel(Static):
    """Bottom-left: event logs."""

    def update_state(self, state: State) -> None:
        events = state.log.events[-100:]
        messages = []
        for event in reversed(events):
            el = event.__rich__()
            if el:
                messages.append(el)
                if len(messages) == 10:
                    break

        renderable = Group(*messages)
        self.update(renderable)
