from pydantic import BaseModel, Field

from agent.actions.base import Action
from agent.character.character import Character, Party
from agent.logs.events import Event, EventType
from agent.logs.log_registry import get_log_registry
from agent.models.position import Position

CELL_WIDTH = 2

registry = get_log_registry()


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

    def append_title_log(self, message: str, event_type: EventType = EventType.HEADER) -> None:
        """Log an event as header."""
        event = Event(message=message, type=event_type)
        registry.append(event)

    def log_event(self, message: str, event_type: EventType = EventType.DETAIL, icon: str = "") -> None:
        """Log an event."""
        event = Event(message=message, type=event_type, icon=icon, show_ai=False)
        registry.append(event)

    def log_newline(self) -> None:
        """Log a newline."""
        event = Event(message="", type=EventType.CUSTOM)
        registry.append(event)

    def draw_map(self) -> None:
        # The chosen char aligns well with emoticons
        grid = [["· " for _ in range(self.map_width)] for _ in range(self.map_height)]

        for char in self.alive_characters.values():
            grid[char.pos.y][char.pos.x] = char.icon

        map_str = "\n".join(" ".join(row) for row in grid)
        map_event = Event(message=map_str, actor_id=None, type=EventType.MAP)
        registry.append(map_event)

    def hide_last_event(self, event_type: EventType = EventType.MAIN) -> None:
        for event in reversed(registry.events):
            if event.type == event_type:
                event.show_ai = False
                return
