from datetime import UTC, datetime

from pydantic import BaseModel


class Event(BaseModel):
    actor_id: str | None = None
    actor_icon: str | None = None
    message: str
    turn: str
    type: str = "system"
    timestamp: datetime = datetime.now(tz=UTC)

    def __str__(self) -> str:
        if self.type == "actor":
            return f"Turn {self.turn} {self.actor_icon} -> {self.message}"
        if self.type == "system":
            return f"Turn {self.turn} -> {self.message}"
        return self.message
