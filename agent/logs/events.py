import re
from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel
from rich.text import Text


class Icon:
    ATTACK = "⚔️"
    DAMAGE = "💥"
    DEATH = "☠️"
    DEFENSE = "🛡️ "
    ROLL = "🎲"
    MOVE = "🏃"
    STEALTH = "🥷"
    EFFECT_APPLIED = "🌀"
    EFFECT_EXPIRED = "✨"
    AI = "🤖"


class LogLevel(str, Enum):
    HEADER = "header"  # Narrative main events
    MAIN = "main"  # Narrative main events
    DETAIL = "detail"  # Step-by-step debug info
    SYSTEM = "system"  # Global system events
    MAP = "map"  # Map / spatial events (optional)
    CUSTOM = "custom"
    DEBUG = "debug"


class Verbosity:
    MAIN = 0
    DETAIL = 1
    DEBUG = 2


class Event(BaseModel):
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

    def _highlight_numbers(self, text: str) -> str:
        """Highlight numbers in bold yellow for readability."""
        return re.sub(r"(\d+)", r"[bold yellow]\1[/bold yellow]", text)

    def __rich__(self) -> Text | None:
        color = self._color_for_actor()
        msg = self._highlight_numbers(self.message)
        result = Text(msg)

        # Event formatting based on type
        if self.type == LogLevel.HEADER:
            header_line = Text(self.message, style=f"bold {color}")
            separator = Text("─" * 40, style="dim")
            result = Text.assemble("\n", header_line, "\n", separator)

        elif self.type == LogLevel.MAIN:
            icon = self.icon or "👤"
            result = Text.from_markup(f"[bold {color}]{icon} → {msg}[/bold {color}]")

        elif self.type in {LogLevel.DETAIL, LogLevel.DEBUG}:
            ai_icon = f"({Icon.AI})" if self.show_ai else ""
            result = Text.from_markup(f"    [dim]{self.icon} {msg} {ai_icon}[/dim]")

        elif self.type == LogLevel.SYSTEM:
            result = Text.from_markup(f"\n[bold yellow]⚙️ {msg}[/bold yellow]")

        elif self.type == LogLevel.MAP:
            separator = Text("─" * 40, style="dim")
            result = Text.assemble(msg, "\n", separator)

        return result

    def __str__(self) -> str:
        return f"{self.actor_id or 'system'}: {self.message}"
