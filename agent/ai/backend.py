import random
import uuid
from typing import get_args

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from agent.ai.character_creation.agent import CharacterCreationAgent
from agent.ai.combat_graph import build_combat_graph
from agent.character.character import Character, Party
from agent.equipment.base import EquipmentSlot
from agent.equipment.weapons import MeleeWeapon, WeaponType
from agent.exceptions import CharacterCreationError, InvalidPhaseError
from agent.jobs.fighter import Fighter
from agent.logs.log_event import Icon, LogLevel
from agent.models.config import Config
from agent.models.damage import DamageType
from agent.models.enums import TargetingType
from agent.models.map import GameMap
from agent.models.position import Direction, Position
from agent.models.state import GamePhase, GameResult, GameSnapshot, State
from agent.services.equipment_service import EquipmentService


class GameBackend:
    """
    Manages the full game lifecycle: character creation → story → combat.

    This class orchestrates the game flow between different phases and maintains the game state
    throughout the session. Supports starting from any phase for save/resume functionality.
    """

    DEFAULT_RECURSION_LIMIT = 20
    MAX_PARTY_SIZE = 4

    def __init__(self, initial_state: State, config: Config) -> None:
        self.config = config
        self.initial_state = initial_state.model_copy(deep=True)
        self.recursion_limit = self.DEFAULT_RECURSION_LIMIT
        self.thread_id = str(uuid.uuid4())
        self.phase = GamePhase.START

        # Current game state
        self.state: State = initial_state.model_copy(deep=True)

        # Initialize AI agents
        self.combat_graph = build_combat_graph(config=config.agent)
        self.char_agent = CharacterCreationAgent(config=self.config.agent, max_players=self.config.max_players)

        # Cache default enemies
        self._default_enemy_party = Party(id="p2", name="Goblins", is_player_party=False)

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

    def create_snapshot(self) -> GameSnapshot:
        """Create a complete snapshot of the current game state."""
        return GameSnapshot(
            state=self.state.model_copy(deep=True),
            phase=self.phase,
            thread_id=self.thread_id,
            recursion_limit=self.recursion_limit,
            char_creation_state=self.char_agent.create_snapshot(),
        )

    def load_snapshot(self, snapshot: GameSnapshot) -> None:
        """Load a game snapshot, restoring all state."""
        self.state = snapshot.state.model_copy(deep=True)
        self.phase = snapshot.phase
        self.thread_id = snapshot.thread_id
        self.recursion_limit = snapshot.recursion_limit
        self.char_agent.load_snapshot(snapshot.char_creation_state)

    def reset(self) -> State:
        """Reset the entire game session to initial state."""
        self.thread_id = str(uuid.uuid4())
        self.phase = GamePhase.START
        self.state = self.initial_state.model_copy(deep=True)
        self.char_agent.reset()
        return self.state

    async def start(self, from_phase: GamePhase | None = None) -> GameResult:
        """Start or resume the game from a specific phase."""
        target_phase = from_phase or GamePhase.CHARACTER_CREATION

        if target_phase == GamePhase.START:
            raise InvalidPhaseError("Cannot start from START phase. Use CHARACTER_CREATION, STORY, or COMBAT.")

        self.phase = target_phase

        # Delegate to phase-specific start methods
        if target_phase == GamePhase.CHARACTER_CREATION:
            return await self._start_character_creation()
        if target_phase == GamePhase.STORY:
            return await self._start_story()
        if target_phase == GamePhase.COMBAT:
            return await self._start_combat_phase()

        msg = f"Unknown phase: {target_phase}"
        raise InvalidPhaseError(msg)

    async def _start_character_creation(self) -> GameResult:
        """Start or resume character creation phase."""
        if not self.char_agent.has_started:
            try:
                message = await self.char_agent.respond(user_input="")
                self._log_dm_message(message)

                return GameResult(output=message, phase=self.phase, state=self.state)
            except Exception as e:
                msg = f"Failed to start character creation: {e}"
                raise CharacterCreationError(msg) from e

        # Resuming existing character creation
        return GameResult(output="Resuming character creation...", phase=self.phase, state=self.state)

    async def _start_story(self) -> GameResult:
        """Start or resume story phase."""
        # Verify we have at least one character
        if not self.state.characters:
            raise InvalidPhaseError("Cannot start story phase without characters. Create a character first.")

        # TODO: Generate story intro from LLM based on current state
        message = "Your adventure begins... What would you like to do?"
        self._log_dm_message(message)

        return GameResult(output=message, phase=self.phase, state=self.state)

    async def _start_combat_phase(self) -> GameResult:
        """Start or resume combat phase."""
        # Verify we have characters and a map
        if not self.state.characters:
            raise InvalidPhaseError("Cannot start combat without characters.")

        if not self.state.map:
            raise InvalidPhaseError("Cannot start combat without a map. Use start_combat() to initialize.")

        # Resume existing combat
        config = self._get_config()
        result = await self.combat_graph.ainvoke(self.state.model_copy(deep=True), config)

        return self._process_combat_result(result)

    async def start_combat(
        self, encounter: list[Character] | None = None, map_layout: list[str] | None = None
    ) -> GameResult:
        """Initialize and start a new combat encounter from any phase."""
        enemies = encounter or self.get_default_enemies()

        # Initialize combat map
        self._initialize_combat_map(enemies, map_layout)

        # Register enemies in state
        for character in enemies:
            self._register_character(character)

        # Transition to combat phase
        self.phase = GamePhase.COMBAT

        # Start combat graph
        config = self._get_config()
        result = await self.combat_graph.ainvoke(self.state.model_copy(deep=True), config)

        return self._process_combat_result(result)

    async def submit_command(self, command: str) -> GameResult:
        """Main input handler. Delegates to the active phase handler."""
        phase_handlers = {
            GamePhase.CHARACTER_CREATION: self._handle_character_creation,
            GamePhase.STORY: self._handle_story,
            GamePhase.COMBAT: self._handle_combat,
        }

        handler = phase_handlers.get(self.phase)
        if handler is None:
            msg = f"Unknown game phase: {self.phase}. Use start() to begin."
            raise InvalidPhaseError(msg)

        try:
            return await handler(command)
        except Exception as e:  # noqa: BLE001
            self._log_error(f"Error handling command in {self.phase.name}: {e}")
            return GameResult(output=f"Error: {e}", phase=self.phase, state=self.state, done=True)

    async def _handle_character_creation(self, command: str) -> GameResult:
        """Handle character creation phase input."""
        message = await self.char_agent.respond(command)
        self._log_dm_message(message)

        interrupt = None

        # Detect completion of a character
        if self.char_agent.current_character:
            character = self.char_agent.current_character.to_character(party=self.char_agent.party_name)
            if character.id not in self.state.characters:
                self._register_character(character)
                interrupt = f"Character {character.name} created!"

        # Continue when done
        if self.char_agent.is_done:
            self.phase = GamePhase.STORY

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
            return await self.start_combat()

        return GameResult(output=command, phase=self.phase, state=self.state)

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

    def _initialize_combat_map(self, encounter: list[Character], map_layout: list[str] | None = None) -> None:
        """
        Initialize the combat map with characters and terrain.

        Note:
            Map generation should eventually be delegated to a DM/map generator
        """
        # Use custom or default map layout
        if map_layout is None:
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

        # Extract all walkable positions and walls
        walls, walkable = [], []
        for y, row in enumerate(map_layout):
            for x, char in enumerate(row):
                pos = Position(x=x, y=y)
                walls.append(pos) if char == "#" else walkable.append(pos)

        directions = get_args(Direction)

        # Shuffle the walkable positions for random placement
        random.shuffle(walkable)

        # Assign a random position and direction to each character
        all_characters = list(self.state.characters.values()) + encounter
        for character in all_characters:
            if walkable:
                character.combat.pos = walkable.pop()
                character.combat.pos.direction = random.choice(directions)  # noqa: S311
            else:
                raise ValueError("Not enough free space on the map for all characters!")

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
            description="Heavy sword",
            damage_dice="2d10",
            damage_type=DamageType.SLASHING,
            weapon_type=WeaponType.MARTIAL_MELEE,
            targeting=TargetingType.SINGLE,
        )

        self._log_dm_message(f"Hero found {sword.name}")

        player_char = self._get_first_player_character()
        if player_char:
            EquipmentService.equip_melee_weapon(player_char, sword, EquipmentSlot.MAIN_HAND)

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
