from collections import defaultdict

from pydantic import BaseModel, Field

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
    visibility: defaultdict[str, list[str]] = Field(default_factory=defaultdict)
    parties: dict[str, Party] = {}
    decision: DecisionResult | None = None
    action: Action | None = None
    verification_result: VerificationResult | None = None
    retries: int = 0
    done: bool = False

    @property
    def alive_characters(self) -> dict[str, Character]:
        return {cid: c for cid, c in self.characters.items() if c.is_alive}

    @property
    def visible_characters(self) -> list[Character]:
        actor = self.current_actor
        return [self.characters[t] for t in self.visibility[actor.id]]

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

    def update_visibility(self, actor: Character) -> None:
        if not self.map:
            raise ValueError

        visible_targets = []
        for target_id, target in self.alive_characters.items():
            if actor.id == target_id:
                continue

            # Check range + line of sight before doing perception
            if not self.map.within_visibility_range(actor, target):
                continue

            # Handle stealth / perception contest
            if not target.is_hidden or actor.detect_target(target, use_passive=True):
                visible_targets.append(target_id)

        self.visibility[actor.id] = visible_targets
