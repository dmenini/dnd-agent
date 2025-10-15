from logging import getLogger

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from agent.models.state import DecisionResult, Event, State

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
            actor.start_turn()

            for effect in actor.status_effects:
                state.append_log(str(effect).format(actor=actor.name))

        actions = actor.available_actions()
        if not actions:
            return state

        actor_str = {
            "id": actor.id,
            "name": actor.name,
            "pos": actor.pos,
            "party": actor.party.model_dump_json(),
            "is_player": actor.is_player,
            "level": actor.level,
            "hp": f"{actor.attributes.hp}/{actor.max_hp}",
            "movement": f"{actor.current_speed}/{actor.speed}",
            "stats": actor.stats.model_dump_json(),
            "available_actions": {id_: val.model_dump_json(exclude_none=True) for id_, val in actions.items()},
        }

        visible_enemies = [
            {
                "id": c.id,
                "name": c.name,
                "pos": c.pos,
                "party": c.party.model_dump_json(),
                "hp": f"{c.attributes.hp}/{c.max_hp}",
                "distance": actor.distance(c.pos),
            }
            for c in state.alive_characters.values()
            if c.id != actor.id
        ]

        history = self.group_messages(
            events=state.event_log,
            player_team={c.id for c in state.get_party_members(actor.party.id)},
        )

        if state.verification_result and not state.verification_result.valid and state.verification_result.input:
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

        return state

    def group_messages(self, events: list[Event], player_team: set[str]) -> list[BaseMessage]:
        """Group sequential events into HumanMessage or AIMessage based on which team the actor belongs to."""
        messages: list[BaseMessage] = []
        current_group: list[str] = []
        current_is_player = None

        for event in events:
            if not event.actor_id:
                continue
            is_player = event.actor_id in player_team
            # Start a new group if this is the first event or if team changes
            if current_is_player is None or is_player != current_is_player:
                if current_group:
                    role = HumanMessage if current_is_player else AIMessage
                    messages.append(role(content="".join(current_group)))
                    current_group = []
                current_is_player = is_player

            # Format the line
            current_group.append(f"{event.actor_id}: {event.message}\n")

        # Append the last group
        if current_group:
            role = HumanMessage if current_is_player else AIMessage
            messages.append(role(content="".join(current_group)))

        return messages
