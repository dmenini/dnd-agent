import operator
from typing import Annotated, Any, List, Literal, Optional

from langchain_core.messages import AnyMessage
from pydantic import BaseModel, Field


class Observation(BaseModel):
    turn: int
    visible_entities: list
    last_event: Optional[str] = None
    pc_state: dict
    map_snapshot: Optional[Any] = None


class Action(BaseModel):
    actor_id: str
    action_type: Literal["attack", "move", "cast_spell", "roleplay", "wait"]
    target_id: Optional[str] = None
    ability: Optional[str] = None
    attack_method: Optional[str] = None
    description: Optional[str] = None
    meta: Optional[dict] = Field(default_factory=dict)


class VerificationResult(BaseModel):
    valid: bool
    reasons: List[str] = Field(default_factory=list)
    adjusted_action: Optional[Action] = None


class CombatResult(BaseModel):
    success: bool
    events: List[str] = Field(default_factory=list)
    new_state: Optional[dict] = None


class State(BaseModel):
    observation: Observation | None = None
    action: Action | None = None
    combat_result: CombatResult | None = None
    verification_result: VerificationResult | None = None


class Context(BaseModel):
    pass
