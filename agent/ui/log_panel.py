from typing import Any

from textual.widgets import RichLog

from agent.models.state import State


class LogPanel(RichLog):
    """Bottom-left: event logs."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(highlight=False, markup=True, wrap=False, **kwargs)
        self._last_rendered_count = 0

    def update_state(self, state: State) -> None:
        messages = state.log.events[-100:]  # keep last 100
        # Only write the new messages since last update
        for message in messages[self._last_rendered_count :]:
            self.write(message)
        self._last_rendered_count = len(messages)

    def clear(self) -> None:
        self.clear()
        self._last_rendered_count = 0
