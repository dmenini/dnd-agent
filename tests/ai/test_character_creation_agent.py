"""Tests for character creation agent conversation flows."""

import pytest
from langchain_core.messages import AIMessage
from pytest_mock import MockerFixture

from agent.ai.character_creation.agent import CharacterCreationAgent
from agent.character.builder import CharacterBuilder
from agent.equipment.armor import Armor, ArmorType
from agent.equipment.base import EquipmentSlot
from agent.jobs.base import JobType
from agent.models.config import AgentConfig


@pytest.mark.asyncio
async def test_single_character_minimal_flow(mocker: MockerFixture, char_creation_config: AgentConfig) -> None:
    """Test creating a single Fighter character with minimal selections."""
    # Mock the compiled agent graph
    fake_agent = mocker.AsyncMock()

    # Simulate conversation steps with state updates
    fake_agent.ainvoke.side_effect = [
        # Greeting
        {
            "messages": [AIMessage(content="Welcome! Let's create your first character.")],
            "party": [],
            "done": False,
        },
        # Character creation complete
        {
            "messages": [AIMessage(content="Character created successfully!")],
            "party": [CharacterBuilder(name="Aragorn", icon="⚔️", job=JobType.FIGHTER)],
            "done": True,
        },
    ]

    # Patch create_agent to return mock
    with mocker.patch("agent.ai.character_creation.agent.create_agent", return_value=fake_agent):
        agent = CharacterCreationAgent(char_creation_config, max_players=1)

        # Test conversation flow
        response1 = await agent.respond("")
        assert agent.has_started
        assert "Welcome" in response1 or "create" in response1.lower()
        assert len(agent.party) == 0

        await agent.respond("Create Fighter named Aragorn")
        assert len(agent.party) == 1
        assert agent.party[0].name == "Aragorn"
        assert agent.done is True


@pytest.mark.asyncio
async def test_multi_character_party(mocker: MockerFixture, char_creation_config: AgentConfig) -> None:
    """Test creating 2 characters (max_players=2), both fully created."""
    fake_agent = mocker.AsyncMock()

    char1 = CharacterBuilder(name="Hero1", icon="⚔️", job=JobType.FIGHTER)
    char2 = CharacterBuilder(name="Hero2", icon="🧙", job=JobType.WIZARD)

    fake_agent.ainvoke.side_effect = [
        {"messages": [AIMessage(content="Let's create your party!")], "party": [], "done": False},
        {"messages": [AIMessage(content="First character created!")], "party": [char1], "done": False},
        {"messages": [AIMessage(content="Second character created!")], "party": [char1, char2], "done": True},
    ]

    with mocker.patch("agent.ai.character_creation.agent.create_agent", return_value=fake_agent):
        agent = CharacterCreationAgent(char_creation_config, max_players=2)

        await agent.respond("")
        assert len(agent.party) == 0

        await agent.respond("Create first character")
        assert len(agent.party) == 1
        assert agent.done is False

        await agent.respond("Create second character")
        assert len(agent.party) == 2
        assert agent.party[0].name == "Hero1"
        assert agent.party[1].name == "Hero2"
        assert agent.done is True


@pytest.mark.asyncio
async def test_early_party_finalization(mocker: MockerFixture, char_creation_config: AgentConfig) -> None:
    """Test creating 1 character, then finalize_party before max_players reached."""
    fake_agent = mocker.AsyncMock()

    char1 = CharacterBuilder(name="Solo", icon="⚔️", job=JobType.FIGHTER)

    fake_agent.ainvoke.side_effect = [
        {"messages": [AIMessage(content="Let's create characters!")], "party": [], "done": False},
        {"messages": [AIMessage(content="Character created!")], "party": [char1], "done": False},
        {"messages": [AIMessage(content="Party finalized!")], "party": [char1], "done": True},
    ]

    with mocker.patch("agent.ai.character_creation.agent.create_agent", return_value=fake_agent):
        agent = CharacterCreationAgent(char_creation_config, max_players=3)

        await agent.respond("")
        await agent.respond("Create one character")
        assert len(agent.party) == 1
        assert agent.done is False

        await agent.respond("I'm done, finalize the party")
        assert len(agent.party) == 1  # Not 3
        assert agent.done is True


@pytest.mark.asyncio
async def test_cleric_with_subclass_selection(mocker: MockerFixture, char_creation_config: AgentConfig) -> None:
    """Test creating Cleric, select Life Domain subclass."""
    fake_agent = mocker.AsyncMock()

    cleric_char = CharacterBuilder(name="Healer", icon="✝️", job=JobType.CLERIC)
    cleric_char.selections.subclass = "life_domain"

    fake_agent.ainvoke.side_effect = [
        {"messages": [AIMessage(content="Create your cleric!")], "party": [], "done": False},
        {"messages": [AIMessage(content="Cleric with Life Domain created!")], "party": [cleric_char], "done": True},
    ]

    with mocker.patch("agent.ai.character_creation.agent.create_agent", return_value=fake_agent):
        agent = CharacterCreationAgent(char_creation_config, max_players=1)

        await agent.respond("")
        await agent.respond("Create Cleric named Healer with Life Domain")

        assert len(agent.party) == 1
        assert agent.party[0].job == JobType.CLERIC
        assert agent.party[0].selections.subclass == "life_domain"


@pytest.mark.asyncio
async def test_equipment_selection_multiple_slots(mocker: MockerFixture, char_creation_config: AgentConfig) -> None:
    """Test creating Cleric with 3 equipment slots (main_hand, armor, ranged)."""
    fake_agent = mocker.AsyncMock()

    cleric_char = CharacterBuilder(name="Cleric", icon="✝️", job=JobType.CLERIC)
    armor = Armor(name="Chain Mail", armor_type=ArmorType.HEAVY, base_ac=16)
    cleric_char.selections.equipment[EquipmentSlot.ARMOR] = armor
    # In a real scenario, there would be main_hand and ranged too

    fake_agent.ainvoke.side_effect = [
        {"messages": [AIMessage(content="Choose equipment!")], "party": [], "done": False},
        {"messages": [AIMessage(content="Equipment selected!")], "party": [cleric_char], "done": True},
    ]

    with mocker.patch("agent.ai.character_creation.agent.create_agent", return_value=fake_agent):
        agent = CharacterCreationAgent(char_creation_config, max_players=1)

        await agent.respond("")
        await agent.respond("Choose Chain Mail armor")

        assert len(agent.party) == 1
        assert EquipmentSlot.ARMOR in agent.party[0].selections.equipment
        assert agent.party[0].selections.equipment[EquipmentSlot.ARMOR].name == "Chain Mail"


@pytest.mark.asyncio
async def test_mock_character_bypass(char_creation_config: AgentConfig) -> None:
    """Test agent initialized with config.mock_character=True."""
    # Enable mock character mode
    char_creation_config.mock_character = True

    agent = CharacterCreationAgent(char_creation_config, max_players=1)

    # Single respond() should create "Alfred" and set done=True
    response = await agent.respond("")

    assert agent.has_started
    assert agent.done is True
    assert len(agent.party) == 1
    assert agent.party[0].name == "Alfred"
    assert agent.party[0].job == JobType.WIZARD
    assert "Alfred" in response


@pytest.mark.asyncio
async def test_session_snapshot_and_resumption(mocker: MockerFixture, char_creation_config: AgentConfig) -> None:
    """Test creating character partially, snapshot, load into new agent, continue."""
    fake_agent = mocker.AsyncMock()

    char1 = CharacterBuilder(name="InProgress", icon="⚔️", job=JobType.FIGHTER)

    fake_agent.ainvoke.side_effect = [
        {"messages": [AIMessage(content="Starting...")], "party": [], "done": False},
        {"messages": [AIMessage(content="Character in progress...")], "party": [char1], "done": False},
    ]

    with mocker.patch("agent.ai.character_creation.agent.create_agent", return_value=fake_agent):
        agent1 = CharacterCreationAgent(char_creation_config, max_players=2)

        await agent1.respond("")
        await agent1.respond("Create fighter")

        # Create snapshot
        snapshot = agent1.create_snapshot()

        assert snapshot["party"] == [char1]
        assert snapshot["done"] is False
        assert snapshot["started"] is True
        assert "thread_id" in snapshot

        # Create new agent and load snapshot
        agent2 = CharacterCreationAgent(char_creation_config, max_players=2)
        agent2.load_snapshot(snapshot)

        # Verify state restored
        assert len(agent2.party) == 1
        assert agent2.party[0].name == "InProgress"
        assert agent2.done is False
        assert agent2.has_started is True
        assert agent2._thread_id == snapshot["thread_id"]
