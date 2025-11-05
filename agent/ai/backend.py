import uuid
from enum import Enum, auto
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from pydantic import BaseModel

from agent.ai.character_generator import CharacterCreationAgent, CharacterCreationState
from agent.ai.combat_graph import build_combat_graph
from agent.character.character import Character, Party
from agent.equipment.weapons import MeleeWeapon, WeaponType
from agent.jobs.fighter import Fighter
from agent.logs.log_event import Icon, LogLevel
from agent.models.config import Config
from agent.models.damage import DamageType
from agent.models.enums import TargetingType
from agent.models.map import GameMap
from agent.models.position import Position
from agent.models.state import State


class GamePhase(Enum):
    START = auto()
    CHARACTER_CREATION = auto()
    STORY = auto()
    COMBAT = auto()


class GameResult(BaseModel):
    """Result from a game backend operation."""

    output: str | None = None
    state: State
    interrupt: Any | None = None
    done: bool = False
    phase: GamePhase | None = None


class GameBackend:
    """Handles the full game lifecycle: character creation → story → combat."""

    def __init__(self, initial_state: State, config: Config) -> None:
        self.config = config
        self.initial_state = initial_state.model_copy(deep=True)
        self.recursion_limit = 20
        self.thread_id = str(uuid.uuid4())
        self.phase = GamePhase.START

        # Dynamic components
        self.state: State = initial_state.model_copy(deep=True)
        self.character_creation_state = CharacterCreationState()

        # Prebuilt combat graph
        self.combat_graph = build_combat_graph(config=config.agent)
        self.char_agent = CharacterCreationAgent(config=self.config.agent)

    def _get_config(self) -> RunnableConfig:
        return RunnableConfig(
            recursion_limit=self.recursion_limit,
            configurable={"thread_id": self.thread_id},
        )

    def reset(self) -> State:
        """Reset entire game session."""
        self.thread_id = str(uuid.uuid4())
        self.phase = GamePhase.CHARACTER_CREATION
        self.state = self.initial_state.model_copy(deep=True)
        return self.state

    async def start(self) -> GameResult:
        """Start the game from character creation."""
        self.phase = GamePhase.CHARACTER_CREATION
        self.character_creation_state.messages.append(
            {
                "role": "user",
                "content": "Greet the player explaining who you are and what's the first step in their journey.",
            }
        )
        result = await self.char_agent.respond(self.character_creation_state)
        message = result.messages[-1]["content"]
        self.state.log.log_event(message=message, icon=Icon.AI, log_type=LogLevel.MAIN)
        return GameResult(output=message, phase=self.phase, state=self.state)

    async def submit_command(self, command: str) -> GameResult:
        """Main input handler. Delegates to the active phase."""
        if self.phase == GamePhase.CHARACTER_CREATION:
            return await self._handle_character_creation(command)
        if self.phase == GamePhase.STORY:
            return await self._handle_story(command)
        if self.phase == GamePhase.COMBAT:
            return await self._handle_combat(command)
        return GameResult(interrupt="Unknown game phase", phase=self.phase, state=self.state, done=True)

    async def _handle_character_creation(self, command: str) -> GameResult:
        self.character_creation_state.messages.append({"role": "user", "content": command})
        result = await self.char_agent.respond(self.character_creation_state)
        message = result.messages[-1]["content"]

        self.state.log.log_event(message=message, icon=Icon.AI, log_type=LogLevel.MAIN)
        interrupt = None

        if result.done and result.character:
            character = result.character.to_character()
            self.state.characters[character.id] = character
            self.phase = GamePhase.STORY
            interrupt = f"Character {character.name} created!"
            # TODO: allow to create multiple characters

        self.character_creation_state = result

        return GameResult(output=message, interrupt=interrupt, state=self.state, phase=self.phase)

    async def _handle_story(self, command: str) -> GameResult:
        # TODO: handle story by calling LLM
        sword = MeleeWeapon(
            name="Sword",
            description="Heavy sword that may stun the enemy",
            damage_dice="2d10",
            damage_type=DamageType.SLASHING,
            weapon_type=WeaponType.MARTIAL_MELEE,
            targeting=TargetingType.SINGLE,
        )
        self.state.log.log_event(f"Hero found {sword.name}", log_type=LogLevel.MAIN, icon=Icon.AI)
        key = next(iter(self.state.characters.keys()))
        self.state.characters[key].equip_melee_weapon(sword, "main_hand")

        result = {
            "trigger_combat": True,
            "output": command,
        }

        if result["trigger_combat"]:
            enemy_party = Party(id="p2", name="Goblins", is_player_party=False)
            enemies = [
                Character(
                    id="orc_1",
                    name="Orc Grunt",
                    icon="👹",
                    pos=Position(x=8, y=3, direction="W"),
                    job=Fighter,
                    party=enemy_party,
                ),
            ]
            return await self._start_combat(encounter=enemies)

        return GameResult(output=str(result["output"]), phase=self.phase, state=self.state)

    async def _start_combat(self, encounter: list[Character]) -> GameResult:
        # TODO: Map has to be generated by DM
        self.phase = GamePhase.COMBAT
        map_str = [
            "############",
            "#..........#",
            "#...###....#",
            "#...###....#",
            "#..........#",
            "#..........#",
            "#..#..##...#",
            "#####.######",
        ]

        chars = list(self.state.characters.values()) + encounter
        walls = [Position(x=x, y=y) for y, row in enumerate(map_str) for x, ch in enumerate(row) if ch == "#"]
        self.state.map = GameMap(
            map="\n".join(map_str),
            width=self.config.map_size[0],
            height=self.config.map_size[1],
            walls=walls,
            characters={c.id: c.pos for c in chars},
            icons={c.id: c.icon for c in chars},
        )

        # Register in state
        self.state.characters.update({c.id: c for c in encounter})
        self.state.parties.update({c.party.id: c.party for c in encounter})

        config = self._get_config()
        result = await self.combat_graph.ainvoke(self.state.model_copy(deep=True), config)

        return self._process_combat_result(result)

    async def _handle_combat(self, command: str) -> GameResult:
        config = self._get_config()

        # Resume the last interrupt
        result = await self.combat_graph.ainvoke(Command(resume=command), config)
        state = State.model_validate(result)

        # If the combat continues
        if not state.done:
            result = await self.combat_graph.ainvoke(state, config)

        combat_result = self._process_combat_result(result)

        if combat_result.done:
            self.phase = GamePhase.STORY
            combat_result.output = "Combat ended. The story continues..."
            combat_result.phase = self.phase

        return combat_result

    def _process_combat_result(self, result: dict) -> GameResult:
        self.state = State.model_validate(result)
        interrupt = result.get("__interrupt__")
        return GameResult(
            state=self.state,
            interrupt=interrupt[0].value if interrupt else None,
            done=self.state.done,
            phase=self.phase,
        )
