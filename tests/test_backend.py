from typing import Any

import pytest
from pytest_mock import MockerFixture, MockType

from agent.ai.backend import GameBackend
from agent.ai.character_creation.agent import DEFAULT_PARTY_NAME
from agent.character.builder import CharacterBuilder
from agent.character.character import Character
from agent.exceptions import InvalidPhaseError
from agent.jobs.base import JobType
from agent.logs.log_event import LogLevel
from agent.models.config import AgentConfig, Config
from agent.models.map import GameMap
from agent.models.position import Position
from agent.models.state import GamePhase, GameResult, State


@pytest.fixture
def mock_combat_graph_passthrough(mocker: MockerFixture) -> MockType:
    """Create a mock combat graph that passes through the state."""
    fake_graph = mocker.AsyncMock()

    async def passthrough_mock(state_arg: State, *args: Any, **kwargs: Any) -> dict:
        return state_arg.model_dump()

    fake_graph.ainvoke.side_effect = passthrough_mock
    return fake_graph


@pytest.fixture
def backend(
    config: AgentConfig,
    mock_combat_graph_passthrough: MockType,
) -> GameBackend:
    """Create a game backend with mocked agents."""
    backend = GameBackend(State(), Config(agent=config))
    backend.combat_graph = mock_combat_graph_passthrough
    return backend


@pytest.mark.asyncio
async def test_full_game_flow(config: AgentConfig, mocker: MockerFixture) -> None:
    """Test full game flow from character creation through combat."""
    state = State()

    fake_combat_graph = mocker.AsyncMock()
    fake_combat_graph.ainvoke.side_effect = [
        {
            "__interrupt__": [],
            "done": False,
            "some_field": "combat start",
        },
        {
            "__interrupt__": [],
            "done": False,
            "some_field": "combat resume",
        },
        {
            "__interrupt__": [],
            "done": False,
            "some_field": "combat continue",
        },
        {
            "__interrupt__": [],
            "done": False,
            "some_field": "combat resume",
        },
        {
            "__interrupt__": [],
            "done": True,
            "some_field": "after combat",
        },
    ]
    fake_char_agent = mocker.AsyncMock()
    fake_char_agent.respond = mocker.AsyncMock()
    fake_char_agent.respond.side_effect = ["Welcome to your adventure!", "Here is your character!"]
    fake_char_agent.has_started = False
    fake_char_agent.party_name = DEFAULT_PARTY_NAME

    backend = GameBackend(state, Config(agent=config))
    backend.char_agent = fake_char_agent
    backend.combat_graph = fake_combat_graph

    # Character creation
    result: GameResult = await backend.start()
    assert result.phase == GamePhase.CHARACTER_CREATION
    assert result.state == state

    logs = [e.message for e in state.log.events if e.type == LogLevel.MAIN]
    assert "Welcome to your adventure!" in logs

    fake_char_agent.is_done = True
    fake_char_agent.current_character = CharacterBuilder(name="name", icon="", job=JobType.FIGHTER)
    result = await backend.submit_command("create hero")
    assert "created" in (result.interrupt or "").lower()
    logs = [e.message for e in state.log.events]
    assert "Here is your character!" in logs

    # Story phase
    backend.phase = GamePhase.STORY
    result = await backend.submit_command("explore the dungeon")
    assert result.phase == GamePhase.COMBAT  # because combat starts
    assert backend.phase == GamePhase.COMBAT

    # Combat phase
    result = await backend.submit_command("attack goblin")
    assert result.done is False
    assert backend.phase == GamePhase.COMBAT

    result = await backend.submit_command("attack goblin")
    assert result.done
    assert backend.phase == GamePhase.STORY


@pytest.mark.asyncio
async def test_start_from_character_creation(config: AgentConfig, mocker: MockerFixture) -> None:
    """Test starting explicitly from character creation phase."""
    state = State()

    fake_char_agent = mocker.AsyncMock()
    fake_char_agent.respond.return_value = "Let's create your character!"
    fake_char_agent.has_started = False

    backend = GameBackend(state, Config(agent=config))
    backend.char_agent = fake_char_agent

    result = await backend.start(from_phase=GamePhase.CHARACTER_CREATION)

    assert result.phase == GamePhase.CHARACTER_CREATION
    assert backend.phase == GamePhase.CHARACTER_CREATION
    assert "Let's create your character!" in (result.output or "")


@pytest.mark.asyncio
async def test_start_from_story_phase(backend: GameBackend, config: AgentConfig, actor: Character) -> None:
    """Test starting from story phase with existing character."""
    backend.state.characters[actor.id] = actor

    result = await backend.start(from_phase=GamePhase.STORY)

    assert result.phase == GamePhase.STORY
    assert backend.phase == GamePhase.STORY
    assert result.output is not None


@pytest.mark.asyncio
async def test_start_from_story_without_characters_fails(backend: GameBackend) -> None:
    """Test that starting story phase without characters raises error."""
    with pytest.raises(InvalidPhaseError, match="without characters"):
        await backend.start(from_phase=GamePhase.STORY)


@pytest.mark.asyncio
async def test_start_from_combat_phase(backend: GameBackend, actor: Character) -> None:
    """Test starting from combat phase with existing combat state."""
    backend.state.characters[actor.id] = actor

    # Setup existing combat map
    map_layout = [
        "######",
        "#....#",
        "#....#",
        "######",
    ]
    backend.state.map = GameMap(
        map="\n".join(map_layout),
        width=6,
        height=4,
        walls=[Position(x=x, y=y) for y, row in enumerate(map_layout) for x, ch in enumerate(row) if ch == "#"],
        characters={actor.id: actor.pos},
        icons={actor.id: actor.icon},
    )

    result = await backend.start(from_phase=GamePhase.COMBAT)

    assert result.phase == GamePhase.COMBAT
    assert backend.phase == GamePhase.COMBAT
    backend.combat_graph.ainvoke.assert_called_once()


@pytest.mark.asyncio
async def test_start_from_combat_without_map_fails(backend: GameBackend, actor: Character) -> None:
    """Test that starting combat phase without a map raises error."""
    backend.state.characters[actor.id] = actor

    with pytest.raises(InvalidPhaseError, match="without a map"):
        await backend.start(from_phase=GamePhase.COMBAT)


@pytest.mark.asyncio
async def test_start_from_start_phase_fails(backend: GameBackend) -> None:
    """Test that starting from START phase raises error."""
    with pytest.raises(InvalidPhaseError, match="Cannot start from START phase"):
        await backend.start(from_phase=GamePhase.START)


@pytest.mark.asyncio
async def test_start_combat_from_any_phase(backend: GameBackend, actor: Character, target: Character) -> None:
    """Test that start_combat can initialize combat from any phase."""
    backend.state.characters[actor.id] = actor
    backend.phase = GamePhase.STORY  # Start from story phase

    enemies = [target]

    result = await backend.start_combat(encounter=enemies)

    assert result.phase == GamePhase.COMBAT
    assert backend.phase == GamePhase.COMBAT

    # Verify ainvoke was called
    assert backend.combat_graph.ainvoke.call_count == 1

    # Get the state that was passed to ainvoke
    call_args = backend.combat_graph.ainvoke.call_args
    state_arg = call_args[0][0]

    assert state_arg.map is not None
    assert actor.id in state_arg.map.characters
    assert target.id in state_arg.map.characters


@pytest.mark.asyncio
async def test_start_combat_map_initialization(
    backend: GameBackend, actor: Character, target: Character, mocker: MockerFixture
) -> None:
    """Test that combat graph is called with properly initialized map."""
    backend.state.characters[actor.id] = actor

    custom_map = [
        "####",
        "#..#",
        "#..#",
        "####",
    ]

    enemies = [target]

    await backend.start_combat(encounter=enemies, map_layout=custom_map)

    # Verify ainvoke was called
    assert backend.combat_graph.ainvoke.call_count == 1

    # Get the state that was passed to ainvoke
    call_args = backend.combat_graph.ainvoke.call_args
    state_arg = call_args[0][0]  # First positional argument

    # Verify the state has the custom map
    assert state_arg.map is not None
    assert state_arg.map.map == "\n".join(custom_map)

    # Verify both characters are in the map
    assert actor.id in state_arg.map.characters
    assert target.id in state_arg.map.characters

    # Verify walls were extracted correctly (corners and edges)
    assert len(state_arg.map.walls) == 12  # All '#' characters in 4x4 border


def test_create_snapshot(backend: GameBackend, actor: Character) -> None:
    """Test creating a game snapshot."""
    backend.state.characters[actor.id] = actor
    backend.phase = GamePhase.STORY
    backend.thread_id = "test-thread-123"

    snapshot = backend.create_snapshot()

    assert snapshot.phase == GamePhase.STORY
    assert snapshot.thread_id == "test-thread-123"
    assert snapshot.state.model_dump() == backend.state.model_dump()
    assert snapshot.recursion_limit == backend.DEFAULT_RECURSION_LIMIT


def test_load_snapshot(config: AgentConfig, actor: Character) -> None:
    """Test loading a game snapshot."""
    # Create original backend
    state = State()
    state.characters[actor.id] = actor

    backend1 = GameBackend(state, Config(agent=config))
    backend1.phase = GamePhase.COMBAT
    backend1.thread_id = "original-thread"

    # Create snapshot
    snapshot = backend1.create_snapshot()

    # Load into new backend
    backend2 = GameBackend(State(), Config(agent=config))
    backend2.load_snapshot(snapshot)

    assert backend2.phase == GamePhase.COMBAT
    assert backend2.thread_id == "original-thread"
    assert actor.id in backend2.state.characters
    assert backend2.state.characters[actor.id].name == actor.name


def test_reset(backend: GameBackend, actor: Character) -> None:
    """Test resetting the game backend."""
    backend.state.characters[actor.id] = actor
    backend.initial_state.characters[actor.id] = actor
    backend.phase = GamePhase.COMBAT
    original_thread_id = backend.thread_id
    backend.state.characters[actor.id].name = "Modified Name"

    backend.reset()

    assert backend.phase == GamePhase.START
    assert backend.thread_id != original_thread_id
    assert len(backend.state.characters) == len(backend.initial_state.characters)
    assert backend.state.characters[actor.id].name == backend.initial_state.characters[actor.id].name
    assert len(backend.char_agent.party) == 0


@pytest.mark.asyncio
async def test_resume_character_creation_from_snapshot(config: AgentConfig, mocker: MockerFixture) -> None:
    """Test resuming character creation from a saved snapshot."""
    state = State()

    # Setup backend with partial character creation
    backend1 = GameBackend(state, Config(agent=config))
    backend1.phase = GamePhase.CHARACTER_CREATION

    # Create snapshot
    snapshot = backend1.create_snapshot()

    # Load into new backend
    backend2 = GameBackend(State(), Config(agent=config))
    backend2.load_snapshot(snapshot)

    fake_char_agent = mocker.AsyncMock()
    backend2.char_agent = fake_char_agent

    # Resume character creation
    result = await backend2.start(from_phase=GamePhase.CHARACTER_CREATION)

    assert result.phase == GamePhase.CHARACTER_CREATION
    assert result.output == "Resuming character creation..."


@pytest.mark.asyncio
async def test_error_handling_in_submit_command(config: AgentConfig, actor: Character, mocker: MockerFixture) -> None:
    """Test that errors in phase handlers are caught and returned gracefully."""
    state = State()
    state.characters[actor.id] = actor

    fake_char_agent = mocker.AsyncMock()
    fake_char_agent.respond.side_effect = Exception("Test error")

    backend = GameBackend(state, Config(agent=config))
    backend.char_agent = fake_char_agent
    backend.phase = GamePhase.CHARACTER_CREATION

    result = await backend.submit_command("test command")

    assert "Error" in (result.output or "")
    assert result.done is True


@pytest.mark.asyncio
async def test_default_enemies_are_fresh_each_time(backend: GameBackend, actor: Character) -> None:
    """Test that default_enemies property returns fresh instances each time."""
    backend.state.characters[actor.id] = actor
    enemies1 = backend.get_default_enemies()
    enemies2 = backend.get_default_enemies()

    # Should be different instances
    assert enemies1 is not enemies2
    assert enemies1[0] is not enemies2[0]
    # But same content
    assert enemies1[0].id == enemies2[0].id
    assert enemies1[0].name == enemies2[0].name
