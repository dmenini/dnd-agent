from collections import defaultdict
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from agent.actions.base import Action
from agent.ai.character_generator import CharacterCreationState
from agent.character.character import Character, Party
from agent.logs.log_registry import LogRegistry, get_log_registry
from agent.models.decision import DecisionResult
from agent.models.map import GameMap

registry = get_log_registry()


class VerificationResult(BaseModel):
    valid: bool = True
    reason: str = ""
    input: Any


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
    command: str = ""

    @property
    def alive_characters(self) -> dict[str, Character]:
        return {cid: c for cid, c in self.characters.items() if c.is_alive}

    @property
    def visible_characters(self) -> list[Character]:
        if actor := self.current_actor:
            if actor.id not in self.visibility:
                return []
            return [self.characters[t] for t in self.visibility[actor.id]]
        return []

    @property
    def is_player_turn(self) -> bool:
        return self.current_actor is not None and self.current_actor.is_player

    @property
    def current_actor(self) -> Character | None:
        if not self.turn_order:
            return None
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

    def update_visibility(self, actor: Character) -> None:
        if not self.map:
            raise ValueError

        visible_targets = []
        visible_positions = self.map.get_visible_positions(actor)
        for target_id, target in self.alive_characters.items():
            if actor.id == target_id:
                continue

            # Check target is visible
            if target.pos not in visible_positions:
                continue

            # Handle stealth / perception contest
            if actor.detect_target(target, use_passive=True):
                visible_targets.append(target_id)

        self.visibility[actor.id] = visible_targets


class GamePhase(Enum):
    """Represents the current phase of the game."""

    START = "start"
    CHARACTER_CREATION = "creation"
    STORY = "story"
    COMBAT = "combat"


class GameResult(BaseModel):
    """Result from a game backend operation."""

    output: str | None = None
    state: State
    interrupt: Any | None = None
    done: bool = False
    phase: GamePhase | None = None


class GameSnapshot(BaseModel):
    """Complete snapshot of game state for save/load functionality."""

    state: State
    phase: GamePhase
    thread_id: str
    character_creation_state: CharacterCreationState | None = None
    recursion_limit: int = 20
