from collections.abc import Callable
from typing import Self

from agent.logs.events import Event


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

    def subscribe(self, callback: Callable[[Event], None]) -> None:
        self.subscribers.append(callback)

    def filter(self, *, types: list[str] | None = None, actor_ids: list[int] | None = None) -> list[Event]:
        results = self.events
        if types is not None:
            results = [e for e in results if e.type in types]
        if actor_ids is not None:
            results = [e for e in results if e.actor_id in actor_ids]
        return results
