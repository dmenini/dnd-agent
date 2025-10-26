from collections.abc import Callable
from functools import lru_cache
from typing import Self

from agent.logs.events import Event, LogLevel
from agent.logs.subscribers import rich_printer


class LogRegistry:
    _instance: Self | None = None

    def __init__(self) -> None:
        self.events: list[Event] = []
        self.subscribers: list[Callable[[Event], None]] = []

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def append(self, event: Event) -> None:
        self.events.append(event)
        for subscriber in self.subscribers:
            subscriber(event)

    def log_header(self, message: str) -> None:
        """Log an event as header."""
        event = Event(message=message, type=LogLevel.HEADER)
        self.append(event)

    def log_event(self, message: str, event_type: LogLevel = LogLevel.DETAIL, icon: str = "") -> None:
        """Log an event."""
        event = Event(message=message, type=event_type, icon=icon, show_ai=False)
        self.append(event)

    def log_newline(self) -> None:
        """Log a newline."""
        event = Event(message="", type=LogLevel.CUSTOM)
        self.append(event)

    def subscribe(self, callback: Callable[[Event], None]) -> None:
        self.subscribers.append(callback)

    def filter_for_ai(self, *, types: list[str] | None = None, actor_ids: list[int] | None = None) -> list[Event]:
        results = self.events
        if types is not None:
            results = [e for e in results if e.type in types and e.show_ai]
        if actor_ids is not None:
            results = [e for e in results if e.actor_id in actor_ids and e.show_ai]
        return results

    def hide_last_event(self, event_type: LogLevel = LogLevel.MAIN) -> None:
        for event in reversed(self.events):
            if event.type == event_type:
                event.show_ai = False
                return


@lru_cache
def get_log_registry() -> LogRegistry:
    registry = LogRegistry.instance()
    registry.subscribe(rich_printer)
    return registry
