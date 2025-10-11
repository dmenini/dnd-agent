from logging import getLogger

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from agent.models.state import Action, State

log = getLogger(__name__)


class DecisionNode:
    def __init__(self, llm: BaseChatModel, system_prompt: str) -> None:
        self.llm = llm.with_structured_output(Action)
        self.system_prompt = system_prompt

    def __call__(self, state: State) -> State:
        log.debug(self.__class__.__name__, extra=state.model_dump(mode="json"))

        if state.turn_index == 0:
            state.append_log(f"\n--- Round {state.round} ---")

        actor = state.current_actor

        if not actor.is_alive:
            return state

        visible_enemies = [
            c.model_dump_json(include={"id", "name", "party", "hp", "pos"})
            for c in state.characters.values()
            if c.is_alive and c.id != actor.id
        ]

        ongoing_events = "\n".join([e.message for e in state.event_log if not e.hide])

        user_prompt = (
            f"You are controlling {actor.name}, a character in a D&D-like game with this profile:\n"
            f"{actor.model_dump_json()}\n\n"
            f"Visible entities: {visible_enemies}\n"
            f"Last events:\n{ongoing_events}\n"
        )

        action = self.llm.invoke(
            [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        state.action = action  # type: ignore[assignment]

        # Reset verification
        state.verification_result = None

        return state
