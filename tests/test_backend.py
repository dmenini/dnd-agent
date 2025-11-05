
import pytest
from pytest_mock import MockerFixture

from agent.ai.backend import GameBackend, GamePhase, GameResult
from agent.ai.character_generator import CharacterCreationState
from agent.character.builder import CharacterBuilder
from agent.character.stats import Stats
from agent.jobs.base import JobType
from agent.logs.log_event import Icon, LogLevel
from agent.models.config import AgentConfig, Config
from agent.models.state import State


@pytest.mark.asyncio
async def test_full_game_flow(config: AgentConfig, mocker: MockerFixture) -> None:
    # --- Mock config and state ---
    state = State()
    state.log.log_event = mocker.MagicMock()

    # --- Mock graphs ---
    fake_combat_graph = mocker.AsyncMock()
    fake_combat_graph.ainvoke.return_value = {
        "__interrupt__": [],
        "done": True,
        "some_field": "after combat",
    }

    fake_char_agent = mocker.AsyncMock()
    fake_char_agent.respond = mocker.AsyncMock()
    fake_char_agent.respond.side_effect = [
        CharacterCreationState(
            messages=[{"role": "assistant", "content": "Welcome to your adventure!"}],
            done=False,
        ),
        CharacterCreationState(
            messages=[{"role": "assistant", "content": "Here is your character!"}],
            done=True,
            character=CharacterBuilder(
                name="name",
                icon="",
                party="heros",
                stats=Stats(),
                race="human",
                job=JobType.FIGHTER,
                backstory="",
                personality=[],
                alignment="",
                summary=""
            ),
        ),
    ]

    # --- Patch the backend ---
    backend = GameBackend(state, Config(agent=config))
    backend.char_agent = fake_char_agent
    backend.combat_graph = fake_combat_graph

    # --- Character creation ---
    result: GameResult = await backend.start()
    assert result.phase == GamePhase.CHARACTER_CREATION
    assert result.state == state
    state.log.log_event.assert_called_with(message="Welcome to your adventure!", icon=Icon.AI, log_type=LogLevel.MAIN)

    result = await backend.submit_command("create hero")
    assert "created" in (result.interrupt or "").lower()
    state.log.log_event.assert_called_with(message="Here is your character!", icon=Icon.AI, log_type=LogLevel.MAIN)

    # --- Story phase ---
    backend.phase = GamePhase.STORY
    result = await backend.submit_command("explore the dungeon")
    assert result.phase == GamePhase.COMBAT  # because combat starts
    assert backend.phase == GamePhase.COMBAT

    # --- Combat phase ---
    result = await backend.submit_command("attack goblin")
    assert result.done
    assert backend.phase == GamePhase.STORY  # after combat, returns to story
