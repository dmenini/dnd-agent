from typing import Any

from textual.reactive import reactive
from textual.widgets import ListItem, ListView, Markdown, Static

from agent.logs.events import LogEvent, LogLevel
from agent.models.state import State

WINDOW_SIZE = 100
CACHE_SIZE = 1000


class LogItem:
    """Encapsulates a log event and its rendering logic."""

    def __init__(self, event: LogEvent, *, is_expanded: bool = False, is_child: bool = False) -> None:
        self.event = event
        self.is_expanded = is_expanded
        self.is_child = is_child

    def to_list_item(self) -> ListItem:
        """Convert this LogItem to a Textual ListItem."""
        if self.event.type in {LogLevel.MAIN, LogLevel.SYSTEM}:
            item = ListItem(Markdown(str(self.event)))
        elif self.event.type == LogLevel.HEADER:
            item = ListItem(Markdown(str(self.event)))
            item.disabled = True
        else:
            item = ListItem(Static(str(self.event)))
        return item


class LogPanel(ListView):
    verbosity: reactive[int] = reactive(1)

    BINDINGS = [
        ("space", "toggle_expand", "Toggle expand"),
        ("enter", "toggle_expand", "Toggle expand"),
        ("v", "cycle_verbosity", "Cycle verbosity"),
    ]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._cached_logs: list[LogEvent] = []
        self._expanded_mains: set[str] = set()
        self._main_lookup: dict[int, str] = {}  # index -> parent MAIN id
        self._filtered_logs: list[LogEvent] = []
        self._last_rendered_count = 0
        self._was_at_bottom = True
        self._last_expanded_state: set[str] = set()
        self._last_verbosity = 1

    def update_state(self, state: State) -> None:
        # Track if user was at bottom before update
        self._was_at_bottom = self.scroll_offset.y >= self.max_scroll_y - 10

        logs: list[LogEvent] = state.log.events
        new_logs = logs[self._last_rendered_count :]

        # If no new logs, skip everything
        if not new_logs:
            return

        # Store locally so we can scroll/interact later
        self._cached_logs.extend(new_logs)
        self._last_rendered_count = len(logs)

        # Keep only the last N events for memory
        if len(self._cached_logs) > CACHE_SIZE:
            self._cached_logs = self._cached_logs[-CACHE_SIZE:]

        # Don't clear expansion state - preserve user's view
        self.refresh_logs()

        # Only auto-scroll if user was already at bottom
        if self._was_at_bottom:
            self.scroll_end()

    def _filter_logs(self) -> list[LogEvent]:
        visible: list[LogEvent] = []
        self._main_lookup.clear()

        # Apply verbosity filter first
        logs = self._apply_verbosity_filter(self._cached_logs)

        for idx, event in enumerate(logs):
            if event.type in {LogLevel.MAIN, LogLevel.SYSTEM, LogLevel.HEADER}:
                visible.append(event)

            if event.type == LogLevel.MAIN and event.id in self._expanded_mains:
                sub_idx = idx + 1
                while sub_idx < len(logs) and logs[sub_idx].type in {LogLevel.DETAIL, LogLevel.DEBUG}:
                    visible.append(logs[sub_idx])
                    self._main_lookup[len(visible) - 1] = event.id  # associate sub-item with parent MAIN
                    sub_idx += 1

        return visible

    def refresh_logs(self) -> None:
        old_count = len(self._filtered_logs)
        expansion_changed = self._expanded_mains != self._last_expanded_state
        verbosity_changed = self.verbosity != self._last_verbosity

        new_filtered = self._filter_logs()

        # Full rebuild if expansion or verbosity changed
        if expansion_changed or verbosity_changed:
            self._filtered_logs = new_filtered
            self._last_expanded_state = self._expanded_mains.copy()
            self._last_verbosity = self.verbosity
            self.clear()

            for event in self._filtered_logs:
                is_expanded = event.id in self._expanded_mains
                log_item = LogItem(event, is_expanded=is_expanded)
                self.append(log_item.to_list_item())
        else:
            # Incremental update: only append new items
            new_items = new_filtered[old_count:]
            self._filtered_logs = new_filtered

            for event in new_items:
                is_expanded = event.id in self._expanded_mains
                log_item = LogItem(event, is_expanded=is_expanded)
                self.append(log_item.to_list_item())

    def watch_verbosity(self) -> None:
        """React to verbosity changes."""
        self.refresh_logs()

    def action_cycle_verbosity(self) -> None:
        """Cycle through verbosity levels: 0 (minimal) -> 1 (normal) -> 2 (verbose) -> 0..."""
        self.verbosity = (self.verbosity + 1) % 3

        # Notify user of current verbosity level
        level_names = {0: "Minimal", 1: "Normal", 2: "Verbose"}
        self.notify(f"Verbosity: {level_names[self.verbosity]}")

    def on_list_view_selected(self, _: ListView.Selected) -> None:
        """Handle mouse/click selection."""
        self._toggle_expand_at_index(self.index)

    def action_toggle_expand(self) -> None:
        """Handle keyboard shortcut to toggle expansion."""
        self._toggle_expand_at_index(self.index)

    def _apply_verbosity_filter(self, logs: list[LogEvent]) -> list[LogEvent]:
        """Filter logs based on verbosity level."""
        if self.verbosity == 0:
            # Minimal: only MAIN, SYSTEM, HEADER
            return [e for e in logs if e.type in {LogLevel.MAIN, LogLevel.SYSTEM, LogLevel.HEADER}]
        if self.verbosity == 1:
            # Normal: exclude DEBUG
            return [e for e in logs if e.type in {LogLevel.MAIN, LogLevel.SYSTEM, LogLevel.HEADER, LogLevel.DETAIL}]
        # Verbose (2+): show everything
        return logs

    def _toggle_expand_at_index(self, idx: int | None) -> None:
        """Toggle expansion for the item at the given index."""
        if idx is None or not self._filtered_logs:
            return

        log = self._filtered_logs[idx]

        # Determine main id (either self or parent)
        main_id = log.id if log.type in {LogLevel.MAIN, LogLevel.SYSTEM} else self._main_lookup.get(idx)
        if main_id is None:
            return

        if main_id in self._expanded_mains:
            # Collapse
            self._expanded_mains.remove(main_id)
        else:
            # Expand
            self._expanded_mains.add(main_id)

        self.refresh_logs()

        # Move selection to parent MAIN
        for i, e in enumerate(self._filtered_logs):
            if e.id == main_id:
                self.index = i
                break
