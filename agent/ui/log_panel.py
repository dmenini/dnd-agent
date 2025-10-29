from typing import Any

from rich.console import Group
from textual import on
from textual.app import ComposeResult
from textual.events import Key
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import RichLog, Static

from agent.logs.events import LogEvent, LogLevel
from agent.models.state import State

WINDOW_SIZE = 100
CACHE_SIZE = 1000


class LogDetailScreen(ModalScreen):
    """Modal popup showing full details of a log entry."""

    def __init__(self, events: list[LogEvent]) -> None:
        super().__init__()
        self.events = events

    def compose(self) -> ComposeResult:
        yield Static(Group(*self.events))

    def on_key(self, event: Key) -> None:
        """Close on ESC or Enter."""
        if event.key in ("escape", "enter"):
            self.dismiss()


class LogPanel(RichLog):
    verbosity: int = reactive(1)
    selected_index: int = reactive(0)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(highlight=False, markup=True, wrap=False, **kwargs)
        self._last_rendered_count = 0
        self._cached_logs: list[LogEvent] = []
        self._filtered_logs: list[LogEvent] = []
        self._selectable_indices: list[int] = []

    def update_state(self, state: State) -> None:
        logs: list[LogEvent] = state.log.events
        new_logs = logs[self._last_rendered_count:]

        # Store locally so we can scroll/interact later
        self._cached_logs.extend(new_logs)
        self._last_rendered_count = len(logs)

        # Keep only the last N events for memory
        if len(self._cached_logs) > CACHE_SIZE:
            self._cached_logs = self._cached_logs[-CACHE_SIZE:]

        self._filtered_logs = self._filter_logs(self._cached_logs)
        self._selectable_indices = [i for i, e in enumerate(self._filtered_logs) if e.type == LogLevel.MAIN]

        # Adjust selection if out of bounds
        if self.selected_index >= len(self._selectable_indices):
            self.selected_index = max(0, len(self._selectable_indices) - 1)

        self.refresh_logs()

    def _filter_logs(self, logs: list[LogEvent]) -> list[LogEvent]:
        """Show only HEADER + MAIN."""
        return [event for event in logs if event.type in (LogLevel.HEADER, LogLevel.MAIN)]

    def refresh_logs(self) -> None:
        self.clear()
        for idx, event in enumerate(self._filtered_logs):
            text = event.__rich__()
            # Highlight only if this is the currently selected MAIN
            if idx == self._selectable_indices[self.selected_index]:
                text.stylize("reverse bold")
            self.write(text)

    @on(Key)
    def on_key(self, event: Key) -> None:
        if not self._selectable_indices:
            return

        if event.key == "up":
            self.selected_index = max(0, self.selected_index - 1)
            self.refresh_logs()
        elif event.key == "down":
            self.selected_index = min(len(self._selectable_indices) - 1, self.selected_index + 1)
            self.refresh_logs()
        elif event.key == "enter":
            selected = self._filtered_logs[self._selectable_indices[self.selected_index]]
            self.app.push_screen(LogDetailScreen([selected]))
