from typing import Any

from rich.text import Text
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
    2. Only MAIN logs are selectable by default.
    3. When a MAIN log is expanded, its DETAIL/DEBUG logs become selectable.
    4. Pressing Enter on any selectable log under an expanded MAIN collapses the MAIN.
    """

    verbosity: reactive[int] = reactive(1)
    selected_index: reactive[int | None] = reactive(None)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(highlight=False, markup=True, wrap=True, auto_scroll=False, **kwargs)
        self._last_rendered_count = 0
        self._cached_logs: list[LogEvent] = []
        self._filtered_logs: list[LogEvent] = []
        self._selectable_indices: list[int] = []  # indices of visible logs that can be selected
        self._expanded_mains: set[str] = set()  # ids of MAIN logs that are expanded
        self._main_lookup: dict[int, str] = {}  # maps visible log idx -> parent MAIN id

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

        # Start from the bottom
        if self.selected_index is None:
            self.selected_index = len(self._selectable_indices) - 1

        # Adjust selection if out of bounds
        if self.selected_index >= len(self._selectable_indices):
            self.selected_index = max(0, len(self._selectable_indices) - 1)

        self.refresh_logs()
        self.scroll_end()

    def _filter_logs(self) -> list[LogEvent]:
        """Return logs and determine which lines are selectable."""
        visible: list[LogEvent] = []
        self._main_lookup.clear()

        logs = self._cached_logs
        for idx, event in enumerate(logs):
            if event.type in {LogLevel.MAIN, LogLevel.HEADER}:
                visible.append(event)

            if event.type == LogLevel.MAIN and event.id in self._expanded_mains:
                sub_idx = idx + 1
                while sub_idx < len(logs) and logs[sub_idx].type in {LogLevel.DETAIL, LogLevel.DEBUG}:
                    visible.append(logs[sub_idx])
                    self._main_lookup[len(visible) - 1] = event.id  # associate sub-item with parent MAIN
                    sub_idx += 1

        # Compute selectable indices: MAIN always, expanded DETAIL/DEBUG too
        self._selectable_indices = [
            idx for idx, e in enumerate(visible) if e.type == LogLevel.MAIN or idx in self._main_lookup
        ]

        return visible

    def refresh_logs(self) -> None:
        if self.selected_index is None and self._selectable_indices:
            self.selected_index = len(self._selectable_indices) - 1

        self.clear()
        for idx, event in enumerate(self._filtered_logs):
            text = event.__rich__()
            if self._selectable_indices and idx == self._selectable_indices[self.selected_index]:
                if not isinstance(text, Text):
                    raise TypeError
                text.stylize("reverse bold")
            self.write(text)

    @on(Key)
    def on_key(self, event: Key) -> None:
        if not self._selectable_indices or self.selected_index is None:
            return
        if event.key == "up":
            self.selected_index = max(0, self.selected_index - 1)
            self.refresh_logs()
        elif event.key == "down":
            self.selected_index = min(len(self._selectable_indices) - 1, self.selected_index + 1)
            self.refresh_logs()
        elif event.key == "enter":
            self._handle_collapse_expand()

    def _handle_collapse_expand(self) -> None:
        idx = self._selectable_indices[self.selected_index]
        log = self._filtered_logs[idx]

        # Determine the parent MAIN id
        main_id = log.id if log.type == LogLevel.MAIN else self._main_lookup.get(idx)
        if main_id is None:
            return

        if main_id in self._expanded_mains:
            # Collapse and reset the selection to the parent item
            self._expanded_mains.remove(main_id)
            self.selected_index = next(
                (i for i, e_idx in enumerate(self._selectable_indices) if self._filtered_logs[e_idx].id == main_id), 0
            )
        else:
            self._expanded_mains.add(main_id)

        self._filtered_logs = self._filter_logs()
        self.refresh_logs()
