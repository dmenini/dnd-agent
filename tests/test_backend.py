import pytest
from pytest_mock import MockerFixture

from agent.ai.backend import GameBackend, GamePhase, GameResult
from agent.ai.character_generator import CharacterCreationState
from agent.character.builder import CharacterBuilder
from agent.character.stats import Stats
from agent.jobs.base import JobType
from agent.models.config import AgentConfig, Config
from agent.models.state import State


@pytest.mark.asyncio
async def test_full_game_flow(config: AgentConfig, mocker: MockerFixture) -> None:
    # --- Mock config and state ---
    state = State()

    # --- Mock graphs ---
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
                personality="",
                alignment="",
                summary="",
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

    logs = [e.message for e in state.log.events]
    assert "Welcome to your adventure!" in logs

    result = await backend.submit_command("create hero")
    assert "created" in (result.interrupt or "").lower()
    logs = [e.message for e in state.log.events]
    assert "Here is your character!" in logs

    # --- Story phase ---
    backend.phase = GamePhase.STORY
    result = await backend.submit_command("explore the dungeon")
    assert result.phase == GamePhase.COMBAT  # because combat starts
    assert backend.phase == GamePhase.COMBAT

    # --- Combat phase ---
    result = await backend.submit_command("attack goblin")
    assert result.done is False
    assert backend.phase == GamePhase.COMBAT

    result = await backend.submit_command("attack goblin")
    assert result.done
    assert backend.phase == GamePhase.STORY
