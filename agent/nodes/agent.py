import json

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from agent.models.state import Action, ActionType, State, TurnPhase


class NpcNode:
    def __init__(self, llm: BaseChatModel, system_prompt: str) -> None:
        self.llm = llm
        self.system_prompt = system_prompt

    def __call__(self, state: State) -> State:
        visible = [{"id": c.id, "hp": c.hp, "pos": c.pos} for c in state.characters.values() if c.hp > 0]
        user_prompt = f"Visible entities: {visible}\nYour last event: {state.event_log[-1:]}"
        result = self.llm.invoke(
            [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )

        try:
            parsed = json.loads(result.content)
            state.action = Action(**parsed)
        except ValueError as e:
            print("Parsing failed:", e, result.content)
            state.action = Action(
                actor_id=state.actor_id, action_type=ActionType.WAIT, description="waits for a moment."
            )

        state.phase = TurnPhase.VERIFY
        return state
