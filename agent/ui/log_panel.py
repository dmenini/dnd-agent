from typing import Any

from textual.reactive import reactive
from textual.widgets import ListItem, ListView, Markdown, Static

from agent.logs.events import LogEvent, LogLevel
from agent.models.state import State

WINDOW_SIZE = 100
CACHE_SIZE = 1000


class LogPanel(ListView):
    verbosity: reactive[int] = reactive(1)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._cached_logs: list[LogEvent] = []
        self._expanded_mains: set[str] = set()
        self._main_lookup: dict[int, str] = {}  # index -> parent MAIN id
        self._filtered_logs: list[LogEvent] = []
        self._last_rendered_count = 0

    def update_state(self, state: State) -> None:
        logs: list[LogEvent] = state.log.events
        new_logs = logs[self._last_rendered_count :]

        # Store locally so we can scroll/interact later
        self._cached_logs.extend(new_logs)
        self._last_rendered_count = len(logs)

        # Keep only the last N events for memory
        if len(self._cached_logs) > CACHE_SIZE:
            self._cached_logs = self._cached_logs[-CACHE_SIZE:]

        self._expanded_mains.clear()
        self.refresh_logs()
        self.scroll_end()

    def _filter_logs(self) -> list[LogEvent]:
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

        return visible

    def refresh_logs(self) -> None:
        self._filtered_logs = self._filter_logs()
        self.clear()

        for event in self._filtered_logs:
            if event.type == LogLevel.MAIN:
                item = ListItem(Markdown(str(event)))
            elif event.type == LogLevel.HEADER:
                item = ListItem(Markdown(str(event)))
                item.disabled = True
            else:
                item = ListItem(Static(str(event)))
            self.append(item)

    def on_list_view_selected(self, _: ListView.Selected) -> None:
        if self.index is None or not self._filtered_logs:
            return

        idx = self.index
        log = self._filtered_logs[idx]

        # Determine main id (either self or parent)
        main_id = log.id if log.type == LogLevel.MAIN else self._main_lookup.get(idx)
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
