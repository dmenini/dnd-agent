from pydantic import BaseModel

from agent.models.character import Character
from agent.models.enums import ActionType


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


class DiceRoll(BaseModel):
    expression: str
    rolls: list[int]
    total: int
    raw: int


class Event(BaseModel):
    message: str
    turn: int
    hide: bool = False


class State(BaseModel):
    turn: int = 0
    turn_order: list[str] = []
    turn_index: int = 0
    characters: dict[str, Character] = {}
    action: Action | None = None
    verification_result: VerificationResult | None = None
    roll: DiceRoll | None = None
    event_log: list[Event] = []
    done: bool = False

    @property
    def current_actor(self) -> Character:
        return self.alive_characters[self.turn_order[self.turn_index]]

    @property
    def alive_characters(self) -> dict[str, Character]:
        return {c.id: c for c in self.characters.values() if c.hp > 0}

    def flush_logs(self) -> None:
        for event in self.event_log:
            if not event.hide:
                print(event.message)
                event.hide = True

    def append_log(self, message: str) -> None:
        self.event_log.append(Event(message=message, turn=self.turn))


class Context(BaseModel):
    pass
