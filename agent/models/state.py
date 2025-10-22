from pydantic import BaseModel

from agent.actions.base import Action
from agent.character.character import Character, Party
from agent.logs.events import LogLevel
from agent.logs.log_registry import LogRegistry, get_log_registry
from agent.models.decision import DecisionResult
from agent.models.map import GameMap

CELL_WIDTH = 2

registry = get_log_registry()


class VerificationResult(BaseModel):
    valid: bool = True
    reason: str = ""
    input: Action | None = None


class State(BaseModel):
    round: int = 0
    map: GameMap | None = None
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
        self.log.log_event(message=str(self.map), event_type=LogLevel.MAP)

        # gmap = GameMap(map_width=self.map_width, map_height=self.map_height,
        #               characters={id_: c.pos for id_, c in self.alive_characters.items()}, )
        # gmap.draw_map()
