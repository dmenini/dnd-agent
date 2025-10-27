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
from agent.models.map import GameMap
from agent.models.state import State

log = getLogger(__name__)


class DecisionNode:
    def __init__(self, llm: BaseChatModel, system_prompt: str, max_retries: int = 3, history_size: int = 15) -> None:
        self.llm = llm.with_structured_output(DecisionResult)
        self.system_prompt = system_prompt
        self.max_retries = max_retries
        self.history_size = history_size

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

        actions = self.available_actions(actor)
        if not actions:
            state.action = None
            state.decision = None
            state.verification_result = None
            state.retries = 0
            return state

        wait = DecisionResult(
            action_id="wait", description=f"{actor.name} doesn't play by the rules and is forced to skip turn."
        )
        if state.retries > self.max_retries:
            result = wait
        else:
            result = self.predict_next_action(state, actor, list(actions.values()))

        if result.action_id not in actions:
            result = wait  # fallback to wait if illegal

        state.action = actions[result.action_id]
        state.decision = result

        state.log.log_newline()
        action_names = [a.name for a in actions.values()]
        actor.log_event(result.description, log_type=LogLevel.MAIN)
        actor.log_event(f"Available actions: {action_names}")

        return state

    def predict_next_action(self, state: State, actor: Character, actions: list[Action]) -> DecisionResult:
        if state.map is None:
            raise ValueError

        # Prepare message history from previous main events
        history = self.group_messages(state.log)

        if state.verification_result and not state.verification_result.valid and state.verification_result.input:
            # Hide the previous decision that lead to a validation error for a clean log history
            state.log.hide_last_event(event_type=LogLevel.MAIN)
            validation_event = (
                f"{actor.id}: The previously chosen action '{state.verification_result.input.id}' is invalid:\n"
                f"{state.verification_result.reason}\n\n"
                "Instructions: Review the available actions and your movement. "
                "Choose a legal action that respects range, resources, and targeting constraints. "
                "If no target is in range, consider repositioning, using a different ability, "
                "or skipping the turn strategically."
            )
        else:
            validation_event = ""

        visible_characters = state.visible_characters
        visible_enemies = [c for c in visible_characters if c.party.id != actor.party.id]
        visible_allies = [c for c in visible_characters if c.party.id == actor.party.id]

        user_prompt = (
            f"{validation_event}"
            f"You are controlling **{actor.name}**, an NPC in a tactical D&D-like combat.\n"
            f"---\n"
            f"### Character {actor.icon} (ID: {actor.id})\n"
            f"HP: {actor.attributes.hp}/{actor.max_hp} | Level: {actor.level}\n"
            f"Position: ({actor.pos.x}, {actor.pos.y}) | Facing: {actor.pos.direction}\n"
            f"Movement Remaining: {actor.current_speed}/{actor.speed} m\n"
            f"Hidden: {actor.is_hidden} | Party: {actor.party.name}\n"
            f"Status Effects: {', '.join(str(eff) for eff in actor.status_effects) or 'None'}\n"
            f"Spell Slots: {actor.spell_slots}\n"
            f"Stats: {Stats.model_validate(actor.attributes.model_dump())}\n"
            f"---\n"
            f"### Available Actions\n"
            f"{'\n'.join([str(act) for act in actions])}\n"
            f"---\n"
            f"### Visible Allies\n"
            f"{self.format_characters(visible_allies, state.map, actor)}\n"
            f"---\n"
            f"### Visible Enemies\n"
            f"{self.format_characters(visible_enemies, state.map, actor)}\n"
            f"---\n"
            f"### Map Overview\n"
            f"{state.map}\n"
        )
        return self.llm.invoke(  # type: ignore[return-value]
            [
                SystemMessage(content=self.system_prompt),
                *history,
                HumanMessage(content=user_prompt),
            ]
        )

    def group_messages(self, registry: LogRegistry) -> list[BaseMessage]:
        """Group sequential events into HumanMessage or AIMessage based on which team the actor belongs to."""
        messages: list[BaseMessage] = []
        current_group: list[str] = []
        current_is_player = None

        events = registry.filter_for_ai(types=[LogLevel.MAIN, LogLevel.DETAIL])[-self.history_size :]
        for event in events:
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
                action = action_cls.from_weapon(  # type: ignore[attr-defined]
                    weapon=eq, is_two_handed=actor.two_handed_active, stats=actor.attributes
                )
                all_actions.append(action)

        # Spells (only if slot available)
        all_actions.extend(spell for spell in actor.spells if actor.spell_slots.has_slot(spell.level))

        # Special abilities (can have their own categories)
        all_actions += actor.abilities

        return {action.id: action for action in all_actions if action.is_available(actor.action_economy)}

    def format_characters(self, visible_characters: list[Character], game_map: GameMap, actor: Character) -> str:
        lines = []
        for c in visible_characters:
            dist = game_map.distance(actor.pos, c.pos)
            los = actor.los_distance(c.pos)
            effects = ", ".join(str(e) for e in c.status_effects) or "None"
            lines.append(
                f"- {c.icon} ID={c.id}, name={c.name} (HP {c.attributes.hp}/{c.max_hp}) "
                f"at ({c.pos.x, c.pos.y}) facing {c.pos.direction}, distance={dist}m, LoS={los}m, effects={effects}"
            )
        return "\n".join(lines) or "No one in sight, try to explore the map."
