from pydantic import BaseModel, Field

from agent.actions.base import Action
from agent.character.character import Character, Party
from agent.logs.events import EventType
from agent.logs.log_registry import LogRegistry, get_log_registry
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

    @property
    def log(self) -> LogRegistry:
        return get_log_registry()

    def draw_map(self) -> None:
        # The chosen char aligns well with emoticons
        grid = [["· " for _ in range(self.map_width)] for _ in range(self.map_height)]

        for char in self.alive_characters.values():
            grid[char.pos.y][char.pos.x] = char.icon

        map_str = "\n".join(" ".join(row) for row in grid)
        self.log.log_event(message=map_str, event_type=EventType.MAP)
