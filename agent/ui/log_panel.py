from typing import Any

from rich.console import Group
from textual import on
from textual.app import ComposeResult
from textual.events import Key
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import RichLog, Static

from agent.logs.events import LogEvent, LogLevel, Verbosity
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

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(highlight=False, markup=True, wrap=False, **kwargs)
        self._last_rendered_count = 0
        self._cached_logs: list[LogEvent] = []

    def update_state(self, state: State) -> None:
        logs: list[LogEvent] = state.log.events
        new_logs = logs[self._last_rendered_count :]

        # Store locally so we can scroll/interact later
        self._cached_logs.extend(new_logs)
        self._last_rendered_count = len(logs)

        # Keep only the last N events for memory
        if len(self._cached_logs) > CACHE_SIZE:
            self._cached_logs = self._cached_logs[-CACHE_SIZE:]

        # Clear and re-render filtered view
        self.clear()
        filtered = self._filter_logs(self._cached_logs)
        for event in filtered:
            self.write(event)

    def _filter_logs(self, logs: list[LogEvent]) -> list[LogEvent]:
        """Filter logs by verbosity and window rules."""
        cutoff = max(0, len(logs) - WINDOW_SIZE)
        visible = []

        for idx, event in enumerate(logs):
            # Older than cutoff → show only HEADER + MAIN
            if idx < cutoff:
                if event.type in (LogLevel.HEADER, LogLevel.MAIN):
                    visible.append(event)
            else:
                # Inside last window → filter by verbosity
                if event.type == LogLevel.DEBUG and self.verbosity < Verbosity.DEBUG:
                    continue
                if event.type == LogLevel.DETAIL and self.verbosity < Verbosity.DETAIL:
                    continue
                visible.append(event)
        return visible

    @on(Key)
    def on_key(self, event: Key) -> None:
        """Handle user pressing Enter on a selected log entry."""
        if event.key == "enter":
            # For now just show last event's details
            if self._cached_logs:
                self.app.push_screen(LogDetailScreen(self._cached_logs[-1:]))
