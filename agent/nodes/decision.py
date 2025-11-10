from logging import getLogger

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.types import interrupt

from agent.actions.base import Action
from agent.character.character import Character
from agent.logs.log_event import LogLevel
from agent.logs.log_registry import LogRegistry
from agent.models.decision import DecisionResult
from agent.models.map import GameMap
from agent.models.state import State

log = getLogger(__name__)


class DecisionNode:
    def __init__(
        self,
        llm: BaseChatModel,
        system_prompt: str,
        *,
        max_retries: int = 3,
        history_size: int = 15,
        simulation: bool = False,
        mock_llm: bool = False,
    ) -> None:
        self.llm = llm.with_structured_output(DecisionResult)
        self.system_prompt = system_prompt
        self.max_retries = max_retries
        self.history_size = history_size
        self.simulation = simulation
        self.mock_llm = mock_llm

    async def __call__(self, state: State) -> State:
        log.debug(self.__class__.__name__, extra=state.model_dump(mode="json"))

        if state.current_actor is None or not state.map:
            msg = "Incorrect initialization"
            raise ValueError(msg)

        actor = state.current_actor

        if not actor.is_alive:
            return state

        if not self.simulation:
            if actor.is_player:
                state.command = interrupt(f"What should {actor.name} do? (ENTER to let AI decide)")
            else:
                state.command = interrupt("Enemy's turn, press ENTER to continue")

        actions = actor.get_available_actions()
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
            result = await self.predict_next_action(state, actor, list(actions.values()))

        if result.action_id not in actions:
            result = wait  # fallback to wait if illegal

        state.action = actions[result.action_id]
        state.decision = result

        action_names = [a.name for a in actions.values()]
        actor.log_event(result.description, log_type=LogLevel.MAIN)
        actor.log_event(f"Available actions: {action_names}")

        return state

    async def predict_next_action(self, state: State, actor: Character, actions: list[Action]) -> DecisionResult:
        if state.map is None:
            raise ValueError

        if actor.is_player and not self.simulation:
            # In case of simulation enabled, treat player as the AI
            return await self.get_player_decision(state, actor, actions)

        if not self.mock_llm:
            return await self.get_ai_decision(state, actor, actions)

        # Skip turn as fallback
        return DecisionResult(action_id="wait", description=f"{actor.name} passes turn.")

    async def get_player_decision(self, state: State, actor: Character, actions: list[Action]) -> DecisionResult:
        player_input = state.command

        # Option 1: Exact match
        for action in actions:
            if player_input.strip().lower() in (action.id.lower(), action.name):
                return DecisionResult(action_id=action.id, description=f"{actor.name} chooses to {action.name}.")

        # Option 2: Raw decision (for testing purpose)
        try:
            return DecisionResult.model_validate_json(player_input)
        except ValueError:
            pass

        # Option 3: Natural language command → Action prediction
        if not self.mock_llm:
            return await self.interpret_player_input(state, actor, actions, player_input)

        return DecisionResult(action_id="wait", description=f"{actor.name} passes turn.")

    async def get_ai_decision(self, state: State, actor: Character, actions: list[Action]) -> DecisionResult:
        # Prepare message history from previous main events
        history = self.group_messages(state.log)
        validation = self._format_validation(state)
        user_prompt = (
            f"{validation}"
            f"You are controlling **{actor.name}**, an NPC in a tactical D&D-like combat with the following profile.\n"
            f"---\n"
            f"{self._format_context(state, actor, actions)}"
        )

        return await self.llm.ainvoke(  # type: ignore[return-value]
            [
                SystemMessage(content=self.system_prompt),
                *history,
                HumanMessage(content=user_prompt),
            ]
        )

    async def interpret_player_input(
        self, state: State, actor: Character, actions: list[Action], text: str
    ) -> DecisionResult:
        validation = self._format_validation(state)
        text = text or "No decision provided. Choose the most optimal action for the player."
        user_prompt = (
            f"{validation}\n"
            f"Map the player decision to one of the available actions.\n"
            f"---\n"
            f"### Player decision\n"
            f"{text}\n"
            f"{self._format_context(state, actor, actions)}"
        )
        return await self.llm.ainvoke(  # type: ignore[return-value]
            [
                SystemMessage(content=self.system_prompt),
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

    def _format_validation(self, state: State) -> str:
        if state.verification_result and not state.verification_result.valid and state.verification_result.input:
            # Hide the previous decision that led to a validation error for a clean AI history
            state.log.hide_last_event(event_type=LogLevel.MAIN)
            # Due to Action serialization, the input may be a dict instead of a pydantic model
            prev_inp = state.verification_result.input
            id_ = prev_inp["id"] if isinstance(prev_inp, dict) else prev_inp.id
            return (
                f"The previously chosen action '{id_}' is invalid:\n"
                f"{state.verification_result.reason}\n\n"
                "Instructions: Review the available actions and your movement. "
                "Choose a legal action that respects range, resources, and targeting constraints. "
                "If no target is in range, consider repositioning, using a different ability, "
                "or skipping the turn strategically."
            )
        return ""

    def _format_characters(self, visible_characters: list[Character], game_map: GameMap, actor: Character) -> str:
        lines = []
        for c in visible_characters:
            dist = game_map.distance(actor.pos, c.pos)
            los = actor.los_distance(c.pos)
            lines.append(
                f"- {c.id}: {c.icon} name={c.name} (HP {c.attributes.hp}/{c.max_hp}) "
                f"at ({c.pos.x}, {c.pos.y}) facing {c.pos.direction}, distance={dist} steps, LoS={los}m"
            )
        return "\n".join(lines) or "- No one in sight, try to explore the map.\n"

    def _format_context(self, state: State, actor: Character, actions: list[Action]) -> str:
        if not state.map:
            raise ValueError

        visible_characters = state.visible_characters
        visible_enemies = [c for c in visible_characters if c.party.id != actor.party.id]
        visible_allies = [c for c in visible_characters if c.party.id == actor.party.id]

        return (
            f"### Character {actor}\n"
            f"---\n"
            f"### Available Actions\n"
            f"{'\n'.join([str(act) for act in actions])}\n"
            f"---\n"
            f"### Visible Allies\n"
            f"{self._format_characters(visible_allies, state.map, actor)}\n"
            f"---\n"
            f"### Visible Enemies\n"
            f"{self._format_characters(visible_enemies, state.map, actor)}\n"
            f"---\n"
            f"### Map Overview\n"
            f"{state.map}\n\n"
            f"Walls/obstacles (#): {state.map.walls}\n"
            f"Movement steps available: {actor.current_speed}"
        )
