from logging import getLogger

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from agent.models.action import ActionOption, DecisionResult
from agent.models.state import Action, State

log = getLogger(__name__)


class DecisionNode:
    def __init__(self, llm: BaseChatModel, system_prompt: str) -> None:
        self.llm = llm.with_structured_output(DecisionResult)
        self.system_prompt = system_prompt

    def __call__(self, state: State) -> State:
        log.debug(self.__class__.__name__, extra=state.model_dump(mode="json"))

        if state.turn_index == 0:
            state.append_log(f"\n--- Round {state.round} ---")

        actor = state.current_actor

        if not actor.is_alive:
            return state

        actions = actor.available_actions()
        actor_str = {
            "id": actor.id,
            "name": actor.name,
            "pos": actor.pos,
            "party": actor.party.model_dump_json(),
            "is_player": actor.is_player,
            "level": actor.level,
            "hp": f"{actor.attributes.current_hp}/{actor.max_hp}",
            "movement": f"{actor.attributes.current_movement}/{actor.speed}",
            "stats": actor.stats.model_dump_json(),
            "available_actions": {id_: val.model_dump_json(exclude_none=True) for id_, val in actions.items()},
        }

        visible_enemies = [
            {
                "id": c.id,
                "name": c.name,
                "pos": c.pos,
                "party": c.party.model_dump_json(),
                "hp": f"{c.attributes.current_hp}/{c.max_hp}",
                "distance": actor.distance(c.pos),
            }
            for c in state.characters.values()
            if c.is_alive and c.id != actor.id
        ]

        ongoing_events = "\n".join([e.message for e in state.event_log if not e.hide])

        user_prompt = (
            f"You are controlling {actor.name}, a character in a D&D-like game with this profile:\n"
            f"{actor_str}\n\n"
            f"Visible entities: {visible_enemies}\n"
            f"Last events:\n{ongoing_events}\n"
        )

        result: DecisionResult = self.llm.invoke(  # type: ignore[assignment]
            [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )

        chosen_option: ActionOption = actions[result.action_id]
        state.action = Action(
            **chosen_option.model_dump(),
            actor_id=actor.id,
            target_ids=result.target_ids,
            target_position=result.target_position,
            description=result.description,
        )

        # Reset verification
        state.verification_result = None

        return state
