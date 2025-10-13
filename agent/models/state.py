from pydantic import BaseModel

from agent.models.action import Action
from agent.models.character import Character, Party


class VerificationResult(BaseModel):
    valid: bool = True
    reason: str = ""
    input: Action | None = None


class DiceRoll(BaseModel):
    expression: str
    rolls: list[int]
    total: int
    raw: int


class Event(BaseModel):
    actor_id: str | None = None
    message: str
    turn: int
    hide: bool = False


class State(BaseModel):
    round: int = 0
    turn_order: list[str] = []
    turn_index: int = 0
    characters: dict[str, Character] = {}
    parties: dict[str, Party] = {}
    action: Action | None = None
    verification_result: VerificationResult | None = None
    event_log: list[Event] = []
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

    def flush_logs(self) -> None:
        green = "\033[32m{message}\033[0m"
        for event in self.event_log:
            if not event.hide:
                print(green.format(message=event.message))
                event.hide = True

    def append_log(self, message: str) -> None:
        """Append a log event associated to a certain actor. It will be part of the agent history."""
        self.event_log.append(Event(message=message, turn=self.round, actor_id=self.current_actor.id))

    def append_system_log(self, message: str) -> None:
        """Append a system log event. It will be excluded from the agent history"""
        self.event_log.append(Event(message=message, turn=self.round, actor_id=None))


class Context(BaseModel):
    pass
