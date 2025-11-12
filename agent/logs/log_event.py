import uuid
from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field
from rich.markdown import Markdown
from rich.text import Text


class Icon:
    ATTACK = "⚔️ "
    DAMAGE = "💥 "
    DEATH = "☠️ "
    DEFENSE = "🛡️"
    ROLL = "🎲 "
    MOVE = "🏃 "
    STEALTH = "🥷 "
    EFFECT_APPLIED = "🌀 "
    EFFECT_EXPIRED = "✨ "
    WARNING = "⚠️ "
    AI = "🤖"


class LogLevel(str, Enum):
    HEADER = "header"  # Narrative main events
    MAIN = "main"  # Narrative main events
    DETAIL = "detail"  # Step-by-step debug info
    SYSTEM = "npc"  # Global npc events
    MAP = "map"  # Map / spatial events (optional)
    CUSTOM = "custom"
    DEBUG = "debug"


class Verbosity:
    MAIN = 0
    DETAIL = 1
    DEBUG = 2


class LogEvent(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex.lower())  # Compatible with DOM element id
    actor_id: str | None = None
    icon: str | None = "⚙️"
    message: str
    type: LogLevel = LogLevel.MAIN
    timestamp: datetime = datetime.now(tz=UTC)
    show_ai: bool = False
    actor_name: str | None = None
    is_player: bool | None = None

    def _color_for_actor(self) -> str:
        """Return a color depending on the actor's faction."""
        if self.is_player is True:
            return "cyan"
        if self.is_player is False:
            return "magenta"
        return "white"

    def __str__(self) -> str:
        # Event formatting based on type
        result = self.message

        if self.type == LogLevel.HEADER:
            result = f"### **{result}**"

        elif self.type == LogLevel.MAIN:
            icon = self.icon or "👤"
            result = f"{icon} → {result}"

        elif self.type in {LogLevel.DETAIL, LogLevel.DEBUG}:
            ai_icon = f"({Icon.AI})" if self.show_ai else ""
            result = f"    {self.icon} {result} {ai_icon}"

        return result

    def __rich__(self) -> Text | Markdown | None:
        color = self._color_for_actor()
        msg = str(self)
        result: Text | Markdown

        # Event formatting based on type
        if self.type == LogLevel.HEADER:
            result = Markdown(msg, justify="center", style=color)

        elif self.type == LogLevel.MAIN:
            result = Text.from_markup(f"[bold {color}]{msg}[/bold {color}]")

        elif self.type in {LogLevel.DETAIL, LogLevel.DEBUG}:
            result = Text.from_markup(f"    [dim]{msg}[/dim]")

        elif self.type == LogLevel.MAP:
            result = Text(msg, style=color, justify="center")

        else:
            result = Text(msg)

        return result
