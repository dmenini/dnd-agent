
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from agent.models.state import Action, State


class NpcNode:
    def __init__(self, llm: BaseChatModel, system_prompt: str) -> None:
        self.llm = llm.with_structured_output(Action)
        self.system_prompt = system_prompt

    def __call__(self, state: State) -> State:
        actor = state.current_actor

        visible_enemies = [
            c.model_dump_json(include={"id", "name", "hp", "pos"})
            for c in state.characters.values()
            if c.hp > 0 and c.id != actor.id
        ]

        user_prompt = (
            f"You are controlling {actor.name}, a character in a D&D-like game with this profile:\n"
            f"{actor.model_dump_json()}\n\n"
            f"Visible entities: {visible_enemies}\n"
            f"Last event: {state.event_log[-1:] if state.event_log else 'None'}\n"
        )

        action = self.llm.invoke(
            [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        state.action = action
        return state
