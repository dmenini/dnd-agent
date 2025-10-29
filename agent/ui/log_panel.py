from typing import Any

from textual import on
from textual.events import Key
from textual.reactive import reactive
from textual.widgets import RichLog

from agent.logs.events import LogEvent, LogLevel
from agent.models.state import State

WINDOW_SIZE = 100
CACHE_SIZE = 1000


class LogPanel(RichLog):
    """
    1. HEADER and MAIN logs are always visible.
    2. Only MAIN logs are selectable.
    3. When user press Enter on a selected MAIN log, the panel expands that log to also show
        all subsequent DETAIL/DEBUG logs up to the next MAIN (or the end). These DETAIL/DEBUG
        logs are highlighted normally, not selectable.
    """

    verbosity: reactive[int] = reactive(1)
    selected_index: reactive[int] = reactive(0)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(highlight=False, markup=True, wrap=False, auto_scroll=False, **kwargs)
        self._last_rendered_count = 0
        self._cached_logs: list[LogEvent] = []
        self._filtered_logs: list[LogEvent] = []
        self._selectable_indices: list[int] = []  # indices of MAIN logs in _filtered_logs
        self._expanded_mains: set[int] = set()  # indices of MAIN logs that are expanded

    def update_state(self, state: State) -> None:
        logs: list[LogEvent] = state.log.events
        new_logs = logs[self._last_rendered_count :]

        # Store locally so we can scroll/interact later
        self._cached_logs.extend(new_logs)
        self._last_rendered_count = len(logs)

        # Keep only the last N events for memory
        if len(self._cached_logs) > CACHE_SIZE:
            self._cached_logs = self._cached_logs[-CACHE_SIZE:]

        self._filtered_logs = self._filter_logs()

        # Adjust selection if out of bounds
        if self.selected_index >= len(self._selectable_indices):
            self.selected_index = max(0, len(self._selectable_indices) - 1)

        self.refresh_logs()
        self.scroll_end()

    def _filter_logs(self) -> list[LogEvent]:
        """Return logs with HEADER/MAIN always, and DETAIL/DEBUG for expanded MAINs."""
        visible: list[LogEvent] = []
        logs = self._cached_logs
        idx = 0
        while idx < len(logs):
            event = logs[idx]
            if event.type in {LogLevel.MAIN, LogLevel.HEADER}:
                visible.append(event)

            if event.type == LogLevel.MAIN and idx in self._expanded_mains:
                # Include subsequent DETAIL/DEBUG logs
                sub_idx = idx + 1
                while sub_idx < len(logs) and logs[sub_idx].type in {LogLevel.DETAIL, LogLevel.DEBUG}:
                    visible.append(logs[sub_idx])
                    sub_idx += 1
            idx += 1

        self._selectable_indices = [i for i, e in enumerate(visible) if e.type == LogLevel.MAIN]
        return visible

    def refresh_logs(self) -> None:
        self.clear()
        for idx, event in enumerate(self._filtered_logs):
            text = event.__rich__()
            if self._selectable_indices and idx == self._selectable_indices[self.selected_index]:
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
            # Expand/collapse DETAIL/DEBUG logs for this MAIN
            main_idx = self._selectable_indices[self.selected_index]
            if main_idx in self._expanded_mains:
                self._expanded_mains.remove(main_idx)
            else:
                self._expanded_mains.add(main_idx)
            self._filtered_logs = self._filter_logs()
            self.refresh_logs()
