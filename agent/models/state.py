from pydantic import BaseModel, Field, computed_field

from agent.actions.base import Action
from agent.character.character import Character, Party
from agent.logs.events import LogLevel
from agent.logs.log_registry import LogRegistry, get_log_registry
from agent.models.enums import TargetingType
from agent.models.position import Position

CELL_WIDTH = 2

registry = get_log_registry()


class VerificationResult(BaseModel):
    valid: bool = True
    reason: str = ""
    input: Action | None = None


class DecisionResult(BaseModel):
    action_id: str = Field(..., description="ID of the action to take")

    # Map of target ID → number of hits assigned
    target_hits: dict[str, int] = Field(
        default_factory=dict,
        description=(
            "Mapping of target IDs to number of hits each target should receive. "
            f"Example for {TargetingType.MULTI} targeting attack (3 total hits): {{'enemy1': 2, 'enemy2': 1}}"
            f"Example for {TargetingType.SINGLE} targeting attack: {{'enemy1': 1}}"
        ),
    )

    target_position: Position | None = Field(
        default=None,
        description="Target position in case of movement actions. It must be within range.",
    )

    description: str = Field(description="Action description for narrative purpose.")

    @computed_field()
    @property
    def total_hits(self) -> int:
        """Total number of hits to perform (sum of all target hits)."""
        return sum(self.target_hits.values())

    @property
    def target_ids(self) -> list[str]:
        """All targeted IDs."""
        return list(self.target_hits.keys())


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
        self.log.log_event(message=map_str, event_type=LogLevel.MAP)
