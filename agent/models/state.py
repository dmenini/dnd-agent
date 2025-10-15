from pydantic import BaseModel, Field
from rich.console import Console
from rich.table import Table
from rich.text import Text

from agent.actions.base import Action
from agent.character.character import Character, Party
from agent.models.position import Position

CELL_WIDTH = 2

console = Console()


class VerificationResult(BaseModel):
    valid: bool = True
    reason: str = ""
    input: Action | None = None


class DecisionResult(BaseModel):
    action_id: str = Field(description="ID of the action to take")
    target_ids: list[str] = Field(
        default=[],
        description=(
            "IDs of the targets to attack for attack actions. Targets must be within range. "
            "Multiple targets can be attacked only with area actions."
        ),
    )
    target_position: Position | None = Field(
        default=None,
        description="Target position in case of movement actions. It must be within range.",
    )
    description: str = Field(description="Action description for narrative purpose.")


class Event(BaseModel):
    actor_id: str | None = None
    message: str
    turn: int
    hide: bool = False


class State(BaseModel):
    round: int = 0
    map_height: int = 10
    map_width: int = 10
    turn_order: list[str] = []
    turn_index: int = 0
    characters: dict[str, Character] = {}
    parties: dict[str, Party] = {}
    decision: DecisionResult | None = None
    action: Action | None = None
    verification_result: VerificationResult | None = None
    event_log: list[Event] = []
    done: bool = False

    @property
    def alive_characters(self) -> dict[str, Character]:
        return {cid: c for cid, c in self.characters.items() if c.is_alive}

    @property
    def current_actor(self) -> Character:
        return self.characters[self.turn_order[self.turn_index]]

    def get_party_members(self, party_id: str, *, alive_only: bool = False) -> list[Character]:
        """Get members of a party."""
        members = [c for c in self.characters.values() if c.party.id == party_id]
        if alive_only:
            members = [m for m in members if m.is_alive]
        return members

    def append_log(self, message: str) -> None:
        """Append a log event associated to a certain actor. It will be part of the agent history."""
        actor = self.current_actor
        message = f"Turn {self.round + 1}.{self.turn_index + 1} {actor.icon} -> {message}"
        event = Event(message=message, turn=self.round, actor_id=actor.id)
        self.event_log.append(event)

        text = Text(event.message, style="bold green")
        console.print(text)

    def append_system_log(self, message: str) -> None:
        """Append a system log event. It will be excluded from the agent history"""
        message = f"Turn {self.round + 1}.{self.turn_index + 1} -> {message}"
        event = Event(message=message, turn=self.round, actor_id=None)
        self.event_log.append(event)

        text = Text(event.message, style="bold yellow")
        console.print(text)

    def draw_map(self) -> None:
        # The chosen char aligns well with emoticons
        grid = [["· " for _ in range(self.map_width)] for _ in range(self.map_height)]

        for char in self.alive_characters.values():
            grid[char.pos.y][char.pos.x] = char.icon

        table = Table(box=None, show_header=True, show_footer=True)
        for row in grid:
            table.add_row(" ".join(row))

        console.print(table)


class Context(BaseModel):
    pass
