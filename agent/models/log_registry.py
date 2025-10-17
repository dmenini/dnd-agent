from datetime import datetime
from typing import Callable, Self

from pydantic import BaseModel
from rich.console import Console
from rich.text import Text

console = Console()


class Event(BaseModel):
    actor_id: str | None = None
    actor_icon: str | None = None
    message: str
    turn: str
    type: str = "system"
    timestamp: datetime = datetime.now()

    def __str__(self) -> str:
        if self.type == "actor":
            return f"Turn {self.turn} {self.actor_icon} -> {self.message}"
        if self.type == "system":
            return f"Turn {self.turn} -> {self.message}"
        return self.message


class LogRegistry:
    _instance: Self | None = None

    def __init__(self):
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


def rich_printer(event: Event) -> None:
    color = {
        "system": "yellow",
        "map": None,
        "actor": "green",
    }
    text = Text(str(event), style=color[event.type])
    console.print(text)
