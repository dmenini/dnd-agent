from typing import Any

from textual import on
from textual.events import Key
from textual.reactive import reactive
from textual.widgets import Collapsible, ListItem, ListView, Markdown, Static

from agent.logs.events import LogEvent, LogLevel
from agent.models.state import State

WINDOW_SIZE = 100
CACHE_SIZE = 1000


class LogPanel(ListView):
    verbosity: reactive[int] = reactive(1)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._cached_logs: list[LogEvent] = []
        self._last_rendered_count = 0

    def update_state(self, state: State) -> None:
        new_logs = state.log.events[self._last_rendered_count :]
        self._cached_logs.extend(new_logs)
        self._last_rendered_count = len(state.log.events)

        # Keep only last N events
        if len(self._cached_logs) > CACHE_SIZE:
            self._cached_logs = self._cached_logs[-CACHE_SIZE:]

        self.refresh_logs()
        self.scroll_end()

    def refresh_logs(self) -> None:
        self.clear()
        logs = self._cached_logs
        idx = 0
        n = len(logs)

        while idx < n:
            event = logs[idx]

            if event.type == LogLevel.MAIN:
                # Collect children
                children = [
                    Static(str(logs[j])) for j in range(idx + 1, n) if logs[j].type in {LogLevel.DETAIL, LogLevel.DEBUG}
                ]
                collapsible = Collapsible(*children, title=str(event), collapsed=True, disabled=not children)
                self.append(ListItem(collapsible))

                # Skip children
                idx += len(children) + 1

            elif event.type == LogLevel.HEADER:
                self.append(ListItem(Markdown(str(event))))
                idx += 1
            else:
                idx += 1

    @on(Key)
    def on_key(self, event: Key) -> None:
        if self.index is None:
            return

        if event.key == "enter":
            selected_item = self.children[self.index]
            widget = selected_item.children[0]
            if isinstance(widget, Collapsible):
                widget.collapsed = not widget.collapsed
                widget.refresh()
