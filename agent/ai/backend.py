import uuid

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from agent.ai.character_generator import CharacterCreationAgent, CharacterCreationState
from agent.ai.combat_graph import build_combat_graph
from agent.character.character import Character, Party
from agent.equipment.weapons import MeleeWeapon, WeaponType
from agent.exceptions import CharacterCreationError, InvalidPhaseError
from agent.jobs.fighter import Fighter
from agent.logs.log_event import Icon, LogLevel
from agent.models.config import Config
from agent.models.damage import DamageType
from agent.models.enums import TargetingType
from agent.models.map import GameMap
from agent.models.position import Position
from agent.models.state import GamePhase, GameResult, State


class GameBackend:
    """
    Manages the full game lifecycle: character creation → story → combat.

    This class orchestrates the game flow between different phases and maintains
    the game state throughout the session.
    """

    DEFAULT_RECURSION_LIMIT = 20

    def __init__(self, initial_state: State, config: Config) -> None:
        self.config = config
        self.initial_state = initial_state.model_copy(deep=True)
        self.recursion_limit = self.DEFAULT_RECURSION_LIMIT
        self.thread_id = str(uuid.uuid4())
        self.phase = GamePhase.START

        # Current game state
        self.state: State = initial_state.model_copy(deep=True)
        self.character_creation_state = CharacterCreationState()

        # Initialize AI agents
        self.combat_graph = build_combat_graph(config=config.agent)
        self.char_agent = CharacterCreationAgent(config=self.config.agent)

        # Cache default enemies
        self._default_enemy_party = Party(id="enemies", name="Monsters", is_player_party=False)
        self._default_enemies_cache: list[Character] | None = None

    def get_default_enemies(self) -> list[Character]:
        """Lazily create default enemies to avoid mutation issues."""
        return [
            Character(
                id="orc",
                name="Grunt",
                icon="👹",
                pos=Position(x=8, y=3, direction="W"),
                job=Fighter,
                party=self._default_enemy_party,
            ),
        ]

    def _get_config(self) -> RunnableConfig:
        """Generate LangGraph configuration for the current thread."""
        return RunnableConfig(
            recursion_limit=self.recursion_limit,
            configurable={"thread_id": self.thread_id},
        )

    def reset(self) -> State:
        """Reset the entire game session to initial state."""
        self.thread_id = str(uuid.uuid4())
        self.phase = GamePhase.CHARACTER_CREATION
        self.state = self.initial_state.model_copy(deep=True)
        self.character_creation_state = CharacterCreationState()
        return self.state

    async def start(self) -> GameResult:
        """Start the game from character creation phase."""
        self.phase = GamePhase.CHARACTER_CREATION

        greeting_prompt = "Greet the player explaining who you are and what's the first step in their journey."
        self.character_creation_state.messages.append({"role": "user", "content": greeting_prompt})

        try:
            result = await self.char_agent.respond(self.character_creation_state)
            message = result.messages[-1]["content"]
            self._log_dm_message(message)

            return GameResult(output=message, phase=self.phase, state=self.state)
        except Exception as e:
            msg = f"Failed to start game: {e}"
            raise CharacterCreationError(msg) from e

    async def submit_command(self, command: str) -> GameResult:
        """Main input handler. Delegates to the active phase handler."""
        phase_handlers = {
            GamePhase.CHARACTER_CREATION: self._handle_character_creation,
            GamePhase.STORY: self._handle_story,
            GamePhase.COMBAT: self._handle_combat,
        }

        handler = phase_handlers.get(self.phase)
        if handler is None:
            msg = f"Unknown game phase: {self.phase}"
            raise InvalidPhaseError(msg)

        try:
            return await handler(command)
        except Exception as e:  # noqa: BLE001
            self._log_error(f"Error handling command in {self.phase.name}: {e}")
            return GameResult(interrupt=f"Error: {e!s}", phase=self.phase, state=self.state, done=True)

    async def _handle_character_creation(self, command: str) -> GameResult:
        """Handle character creation phase input."""
        self.character_creation_state.messages.append({"role": "user", "content": command})

        result = await self.char_agent.respond(self.character_creation_state)
        message = result.messages[-1]["content"]
        self._log_dm_message(message)

        interrupt = None

        # Check if character creation is complete
        if result.done and result.character:
            character = result.character.to_character()
            self._register_character(character)
            self.phase = GamePhase.STORY
            interrupt = f"Character {character.name} created!"
            # TODO: allow to create multiple characters

        self.character_creation_state = result

        return GameResult(output=message, interrupt=interrupt, state=self.state, phase=self.phase)

    async def _handle_story(self, command: str) -> GameResult:
        """
        Handle story phase input.

        Note:
            This is a placeholder implementation. Should integrate with story LLM.
        """
        # TODO: Integrate with story generation LLM
        self._give_player_starting_equipment()

        # Simulate story decision leading to combat
        trigger_combat = True  # This should come from story LLM

        if trigger_combat:
            return await self._start_combat(encounter=self.get_default_enemies())

        return GameResult(output=command, phase=self.phase, state=self.state)

    async def _start_combat(self, encounter: list[Character]) -> GameResult:
        """Initialize and start a combat encounter."""
        self.phase = GamePhase.COMBAT

        # Initialize combat map
        self._initialize_combat_map(encounter)

        # Register enemies in state
        for character in encounter:
            self._register_character(character)

        # Start combat graph
        config = self._get_config()
        result = await self.combat_graph.ainvoke(self.state.model_copy(deep=True), config)

        return self._process_combat_result(result)

    async def _handle_combat(self, command: str) -> GameResult:
        """Handle combat phase input."""
        config = self._get_config()

        # Resume from interrupt with player's command
        result = await self.combat_graph.ainvoke(Command(resume=command), config)
        state = State.model_validate(result)

        # Continue combat if not done
        if not state.done:
            result = await self.combat_graph.ainvoke(state, config)

        combat_result = self._process_combat_result(result)

        # Transition back to story if combat is complete
        if combat_result.done:
            self.phase = GamePhase.STORY
            # TODO: Let DM summarize combat logs and come up with a final message and give rewards
            message = "Combat ended. The story continues..."
            combat_result.output = message
            combat_result.phase = self.phase
            self._log_dm_message(message)

        return combat_result

    def _process_combat_result(self, result: dict) -> GameResult:
        """Process raw combat graph result into GameResult."""
        self.state = State.model_validate(result)
        interrupt = result.get("__interrupt__")

        return GameResult(
            state=self.state,
            interrupt=interrupt[0].value if interrupt else None,
            done=self.state.done,
            phase=self.phase,
        )

    def _initialize_combat_map(self, encounter: list[Character]) -> None:
        """Initialize the combat map with characters and terrain."""
        # TODO: Generate map dynamically via DM agent
        map_layout = [
            "############",
            "#..........#",
            "#...###....#",
            "#...###....#",
            "#..........#",
            "#..........#",
            "#..#..##...#",
            "#####.######",
        ]

        # Position player character
        player_char = self._get_first_player_character()
        if player_char:
            player_char.pos = Position(x=1, y=1, direction="SE")

        # Collect all characters
        all_characters = list(self.state.characters.values()) + encounter

        # Extract walls from map
        walls = [Position(x=x, y=y) for y, row in enumerate(map_layout) for x, char in enumerate(row) if char == "#"]

        # Create map
        self.state.map = GameMap(
            map="\n".join(map_layout),
            width=self.config.map_size[0],
            height=self.config.map_size[1],
            walls=walls,
            characters={c.id: c.pos for c in all_characters},
            icons={c.id: c.icon for c in all_characters},
        )

    def _register_character(self, character: Character) -> None:
        """Register a character and their party in the game state."""
        self.state.characters[character.id] = character
        self.state.parties[character.party.id] = character.party

    def _give_player_starting_equipment(self) -> None:
        """Give the player character starting equipment."""
        sword = MeleeWeapon(
            name="Sword",
            description="Heavy sword that may stun the enemy",
            damage_dice="2d10",
            damage_type=DamageType.SLASHING,
            weapon_type=WeaponType.MARTIAL_MELEE,
            targeting=TargetingType.SINGLE,
        )

        self._log_dm_message(f"Hero found {sword.name}")

        player_char = self._get_first_player_character()
        if player_char:
            player_char.equip_melee_weapon(sword, "main_hand")

    def _get_first_player_character(self) -> Character | None:
        """Get the first player character from state."""
        if not self.state.characters:
            return None
        return next(iter(self.state.characters.values()))

    def _log_dm_message(self, message: str) -> None:
        """Log an AI message to the game log."""
        self.state.log.log_event(message=message, icon=Icon.AI, log_type=LogLevel.MAIN)

    def _log_error(self, message: str) -> None:
        """Log an error message to the game log."""
        self.state.log.log_event(message=message, icon=Icon.AI, log_type=LogLevel.SYSTEM)
