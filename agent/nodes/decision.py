import json
from logging import getLogger

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from agent.actions.base import Action
from agent.actions.common.attack import MainHandAttackAction, OffHandAttackAction, RangedAttackAction
from agent.actions.common.dash import DashAction
from agent.actions.common.dodge import DodgeAction
from agent.actions.common.hide import HideAction
from agent.actions.common.move import MovementAction
from agent.actions.common.wait import WaitAction
from agent.character.character import Character
from agent.character.stats import Stats
from agent.logs.events import LogLevel
from agent.logs.log_registry import LogRegistry
from agent.models.decision import DecisionResult
from agent.models.state import State

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

        if not state.map:
            msg = "Map not initialized"
            raise ValueError(msg)

        if actor.turn_done:
            state.log.log_header(f"Turn {state.round + 1}.{state.turn_index + 1} - {actor.name}")
            state.draw_map()
            actor.start_turn()

        state.update_visibility(actor)
        visible_characters = state.visible_characters

        actions = self.available_actions(actor)
        if not actions:
            state.action = None
            state.decision = None
            state.verification_result = None
            return state

        actor_str = {
            "id": actor.id,
            "name": actor.name,
            "hp": f"{actor.attributes.hp}/{actor.max_hp}",
            "position": str(actor.pos),
            "party": actor.party.model_dump_json(),
            "is_player": actor.is_player,
            "is_hidden": actor.is_hidden,
            "level": actor.level,
            "movement_available": f"{actor.current_speed}/{actor.speed} m",
            "stats": Stats.model_validate(actor.attributes.model_dump()).model_dump_json(),
            "status_effects": [str(eff) for eff in actor.status_effects],
            "available_actions": {id_: val.model_dump_json(exclude_none=True) for id_, val in actions.items()},
            "spell_slots": str(actor.spell_slots),
        }

        visible_enemies = [
            {
                "id": c.id,
                "name": c.name,
                "party": c.party.model_dump_json(),
                "hp": f"{c.attributes.hp}/{c.max_hp}",
                "position": str(c.pos),
                "path_length": f"{state.map.distance(actor.pos, c.pos)} m",
                "line_of_sight": f"{actor.los_distance(c.pos)} m",
                "status_effects": [str(eff) for eff in c.status_effects],
            }
            for c in visible_characters
        ]

        history = self.group_messages(state.log)

        if state.verification_result and not state.verification_result.valid and state.verification_result.input:
            # Hide the previous decision that lead to a validation error
            state.log.hide_last_event(event_type=LogLevel.MAIN)
            validation_event = (
                f"{actor.id}: The chosen action ({state.verification_result.input.id}) is invalid "
                f"for the following reasons:\n{state.verification_result.reason}"
            )
        else:
            validation_event = ""

        enemies_str = json.dumps(visible_enemies) if visible_enemies else "No characters in sight, move closer."

        user_prompt = (
            f"{validation_event}\n\n"
            f"You are controlling {actor.name}, a character in a D&D-like game with this profile:\n"
            f"{actor_str}\n\n"
            f"Visible entities: {enemies_str}\n"
            f"Map:\n{state.map}"
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

        state.log.log_newline()
        action_names = [a.name for a in actions.values()]
        actor.log_event(result.description, event_type=LogLevel.MAIN)
        actor.log_event(f"Available actions: {action_names}")

        return state

    def group_messages(self, registry: LogRegistry) -> list[BaseMessage]:
        """Group sequential events into HumanMessage or AIMessage based on which team the actor belongs to."""
        messages: list[BaseMessage] = []
        current_group: list[str] = []
        current_is_player = None

        limit = 30
        events = registry.filter(types=[LogLevel.MAIN])[-limit:]
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

    def available_actions(self, actor: Character) -> dict[str, Action]:
        all_actions: list[Action] = [
            MovementAction(range=actor.current_speed),
            DashAction(range=actor.current_speed),
            DodgeAction(),
            WaitAction(),
            HideAction(),
        ]

        # Equipment-based actions
        equipment_map = [
            (actor.main_hand, MainHandAttackAction),
            (actor.off_hand, OffHandAttackAction),
            (actor.ranged, RangedAttackAction),
        ]

        for eq, action_cls in equipment_map:
            if eq:
                action = action_cls.from_weapon(weapon=eq)  # type: ignore[attr-defined]
                all_actions.append(action)

        # Spells (only if slot available)
        all_actions.extend(spell for spell in actor.spells if actor.spell_slots.has_slot(spell.level))

        # Special abilities (can have their own categories)
        all_actions += actor.abilities

        return {action.id: action for action in all_actions if action.is_available(actor.action_economy)}
