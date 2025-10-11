from pydantic import BaseModel, Field

from agent.models.character import Character
from agent.models.enums import ActionType, TurnPhase


class Action(BaseModel):
    actor_id: str
    action_type: ActionType
    target_id: str | None = None
    ability: str | None = None
    attack_method: str | None = None
    description: str = ""
    dice_expression: str = "1d20"
    meta: dict = {}


class VerificationResult(BaseModel):
    valid: bool
    reasons: list[str] = []
    adjusted_action: Action | None = None


class CombatResult(BaseModel):
    success: bool
    events: list[str] = Field(default_factory=list)
    new_state: dict | None = None


class DiceRoll(BaseModel):
    expression: str
    rolls: list[int]
    total: int
    raw: int


class State(BaseModel):
    turn: int = 0
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
