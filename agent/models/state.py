from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TurnPhase(str, Enum):
    DECIDE = "decide"
    VERIFY = "verify"
    ROLL = "roll"
    EXECUTE = "execute"


class ActionType(str, Enum):
    ATTACK = "attack"
    MOVE = "move"
    CAST_SPELL = "cast_spell"
    ROLEPLAY = "roleplay"
    WAIT = "wait"


class Action(BaseModel):
    actor_id: str
    action_type: ActionType
    target_id: str | None = None
    ability: str | None = None
    attack_method: str | None = None
    description: str = ""
    meta: dict = {}


class VerificationResult(BaseModel):
    valid: bool
    reasons: list[str] = []
    adjusted_action: Action | None = None


class CombatResult(BaseModel):
    success: bool
    events: List[str] = Field(default_factory=list)
    new_state: Optional[dict] = None


class DiceRoll(BaseModel):
    expression: str
    rolls: list[int]
    total: int


class Character(BaseModel):
    id: str
    name: str
    hp: int
    pos: tuple[int, int]
    is_player: bool = False


class State(BaseModel):
    turn: int = 1
    phase: TurnPhase = TurnPhase.DECIDE
    actor_id: str | None = None
    characters: dict[str, Character] = {}
    action: Action | None = None
    verification_result: VerificationResult | None = None
    roll: DiceRoll | None = None
    event_log: list[str] = []
    done: bool = False


class Context(BaseModel):
    pass
