from logging import getLogger

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from agent.logs.events import Event, EventType
from agent.logs.log_registry import get_log_registry
from agent.models.state import DecisionResult, State

log = getLogger(__name__)


class DecisionNode:
    def __init__(self, llm: BaseChatModel, system_prompt: str) -> None:
        self.llm = llm.with_structured_output(DecisionResult)
        self.system_prompt = system_prompt

    def __call__(self, state: State) -> State:
        log.debug(self.__class__.__name__, extra=state.model_dump(mode="json"))

        actor = state.current_actor

        if not actor.is_alive:
            return state

        if actor.turn_done:
            state.append_title_log(f"Turn {state.round + 1}.{state.turn_index + 1} - {actor.name}")
            state.draw_map()
            actor.start_turn()

        actions = actor.available_actions()
        if not actions:
            state.action = None
            state.decision = None
            state.verification_result = None
            return state

        actor_str = {
            "id": actor.id,
            "name": actor.name,
            "pos": str(actor.pos),
            "party": actor.party.model_dump_json(),
            "is_player": actor.is_player,
            "level": actor.level,
            "hp": f"{actor.attributes.hp}/{actor.max_hp}",
            "movement": f"{actor.current_speed}/{actor.speed}",
            "stats": actor.stats.model_dump_json(),
            "status_effects": [str(eff) for eff in actor.status_effects],
            "available_actions": {id_: val.model_dump_json(exclude_none=True) for id_, val in actions.items()},
        }

        visible_enemies = [
            {
                "id": c.id,
                "name": c.name,
                "pos": str(c.pos),
                "party": c.party.model_dump_json(),
                "hp": f"{c.attributes.hp}/{c.max_hp}",
                "distance": actor.distance(c.pos),
                "status_effects": [str(eff) for eff in c.status_effects],
            }
            for c in state.alive_characters.values()
            if c.id != actor.id
        ]

        history = self.group_messages(events=get_log_registry().events)

        if state.verification_result and not state.verification_result.valid and state.verification_result.input:
            # Hide the previous decision that lead to a validation error
            state.hide_last_event(event_type=EventType.MAIN)
            validation_event = (
                f"{actor.id}: The chosen action ({state.verification_result.input.id}) is invalid "
                f"for the following reasons:\n{state.verification_result.reason}"
            )
        else:
            validation_event = ""

        user_prompt = (
            f"{validation_event}\n\n"
            f"You are controlling {actor.name}, a character in a D&D-like game with this profile:\n"
            f"{actor_str}\n\n"
            f"Visible entities: {visible_enemies}\n"
        )

        result: DecisionResult = self.llm.invoke(  # type: ignore[assignment]
            [
                SystemMessage(content=self.system_prompt),
                *history,
                HumanMessage(content=user_prompt),
            ]
        )

        state.action = actions[result.action_id]
        state.decision = result

        # Reset verification
        state.verification_result = None

        state.log_newline()
        action_names = [a.name for a in actions.values()]
        actor.log_event(result.description, event_type=EventType.MAIN)
        actor.log_event(f"Available actions: {action_names}")

        return state

    def group_messages(self, events: list[Event]) -> list[BaseMessage]:
        """Group sequential events into HumanMessage or AIMessage based on which team the actor belongs to."""
        messages: list[BaseMessage] = []
        current_group: list[str] = []
        current_is_player = None

        for event in events:
            if not event.show_ai:
                continue
            is_player = event.is_player
            # Start a new group if this is the first event or if team changes
            if current_is_player is None or is_player != current_is_player:
                if current_group:
                    role = HumanMessage if current_is_player else AIMessage
                    messages.append(role(content="\n".join(current_group)))
                    current_group = []
                current_is_player = is_player

            # Format the line
            current_group.append(str(event))

        # Append the last group
        if current_group:
            role = HumanMessage if current_is_player else AIMessage
            messages.append(role(content="\n".join(current_group)))

        return messages
