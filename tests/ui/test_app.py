import pytest
from pytest_mock import MockerFixture
from textual.widgets import Input

from agent.ai.character_creation.agent import DEFAULT_PARTY_NAME
from agent.character.builder import CharacterBuilder
from agent.character.character import Character
from agent.models.config import AgentConfig, Config
from agent.models.decision import DecisionResult
from agent.models.map import GameMap
from agent.models.position import Position
from agent.models.state import GamePhase, State
from agent.services.action_service import ActionService
from agent.ui.game_ui import GameUI
from agent.ui.log_panel import LogPanel


@pytest.fixture
def ui(config: AgentConfig, actor: Character, target: Character, mocker: MockerFixture) -> GameUI:
    state = State()
    config.decision_node["mock_llm"] = True  # To always wait and pass turn

    ui = GameUI(initial_state=state, config=Config(agent=config))

    fake_char_agent = mocker.MagicMock()
    fake_char_agent.respond = mocker.AsyncMock()
    fake_char_agent.respond.return_value = "Here is your character!"
    fake_char_agent.is_done = True
    fake_char_agent.party_name = DEFAULT_PARTY_NAME
    fake_char_agent.current_character = CharacterBuilder(
        name=actor.name,
        icon=actor.icon,
        job=actor.job.type,
    )
    ui.backend.char_agent = fake_char_agent

    actor.pos = Position(x=0, y=0, direction="E")
    target.pos = Position(x=1, y=0)
    ui.backend.get_default_enemies = mocker.MagicMock(return_value=[target])

    def fake_initialize_map(encounter: list[Character], map_layout: list[str] | None = None) -> None:
        ui.backend.state.characters[actor.id].pos = actor.pos
        game_map = GameMap(
            map="..\n..",
            width=2,
            height=2,
            characters={actor.id: actor.pos, target.id: target.pos},
            icons={actor.id: actor.icon, target.id: target.icon},
        )
        ui.backend.state.map = game_map

    ui.backend._initialize_combat_map = fake_initialize_map
    return ui


@pytest.mark.asyncio
async def test_app(
    ui: GameUI,
    config: AgentConfig,
    actor: Character,
    target: Character,
    game_map: GameMap,
) -> None:
    target.attributes.hp = 1

    async with ui.run_test() as pilot:
        log_panel = pilot.app.query_one("#logs", LogPanel)
        input_widget = pilot.app.query_one("#user-input", Input)
        assert input_widget.placeholder == "Press ENTER to start game..."
        assert ui.backend.phase == GamePhase.START

        # Game starts
        await pilot.click(input_widget)
        await pilot.press("enter")
        assert ui.backend.phase == GamePhase.CHARACTER_CREATION

        # Character is created
        await pilot.press("enter")
        assert len(ui.state.characters) == 1
        assert ui.backend.phase == GamePhase.STORY

        ui.state.turn_order = [actor.id, target.id]

        # Combat starts and interrupt stops execution at player's decision time
        await pilot.press("enter")
        assert ui.backend.phase == GamePhase.COMBAT

        # Actor turn -> wait
        assert actor.name in input_widget.placeholder
        assert ui.state.current_actor is not None
        assert ui.state.current_actor.id == actor.id
        assert log_panel._filtered_logs[-1].message == f"Turn 1.1 - {actor.name}"
        assert ui.state.log.events[-1].message == f"Turn 1.1 - {actor.name}"

        input_widget.value = "wait"
        await pilot.press("enter")

        # Enemy turn -> waits automatically
        assert "Enemy" in input_widget.placeholder
        assert ui.state.current_actor is not None
        assert ui.state.current_actor.id == target.id
        assert log_panel._filtered_logs[-1].message == f"Turn 1.2 - {target.name}"
        assert ui.state.log.events[-1].message == f"Turn 1.2 - {target.name}"
        await pilot.press("enter")

        # Actor turn -> Attack enemy and kills
        assert actor.name in input_widget.placeholder
        assert ui.state.current_actor is not None
        assert ui.state.current_actor.id == actor.id
        assert log_panel._filtered_logs[-1].message == f"Turn 2.1 - {actor.name}"
        assert ui.state.log.events[-1].message == f"Turn 2.1 - {actor.name}"
        input_widget.value = DecisionResult(
            action_id="main_hand_attack", target_hits={target.id: 1}, description="Main attack"
        ).model_dump_json()
        await pilot.press("enter")

        # Enemy turn skipped as it's dead
        assert "Press ENTER to start new game..." in input_widget.placeholder
        assert ui.state.current_actor is not None
        assert ui.state.current_actor.id == actor.id
        assert (
            ui.state.log.events[-2].message
            == f"The players are victorious! Party '{actor.party.name}' stands triumphant!"
        )
        assert ui.state.done is True
        assert ui.backend.phase == GamePhase.STORY

        # Game starts again upon ENTER
        await pilot.press("enter")


@pytest.mark.asyncio
async def test_action_resources_are_used(
    ui: GameUI,
    config: AgentConfig,
    actor: Character,
    target: Character,
    game_map: GameMap,
) -> None:
    num_passives = len(actor.passives)
    num_abilities = len(actor.special_abilities)

    async with ui.run_test() as pilot:
        input_widget = pilot.app.query_one("#user-input", Input)
        assert input_widget.placeholder == "Press ENTER to start game..."

        # Game starts
        await pilot.click(input_widget)
        await pilot.press("enter")
        await pilot.pause()

        # Character is created
        await pilot.press("enter")
        assert len(ui.state.characters) == 1
        ui.state.turn_order = [actor.id, target.id]

        # Combat starts and interrupt stops execution at player's decision time
        await pilot.press("enter")

        # Actor turn -> attack
        assert actor.name in input_widget.placeholder
        input_widget.value = DecisionResult(
            action_id="main_hand_attack", target_hits={target.id: 1}, description="Main attack"
        ).model_dump_json()
        await pilot.press("enter")

        assert ui.state.current_actor is not None
        assert "main_hand_attack" not in ActionService.get_available_actions(ui.state.current_actor)

        # Actor turn -> second wind (due to serialization it may be restored)
        assert actor.name in input_widget.placeholder
        input_widget.value = DecisionResult(action_id="second_wind", description="Second wind").model_dump_json()
        await pilot.press("enter")

        assert ui.state.current_actor is not None
        assert "second_wind" not in ActionService.get_available_actions(ui.state.current_actor)

        # Actor turn -> turn around is free
        new_pos = Position(x=actor.pos.x, y=actor.pos.y, direction="S")
        assert actor.name in input_widget.placeholder
        input_widget.value = DecisionResult(
            action_id="move", target_position=new_pos, description="Turn around"
        ).model_dump_json()
        await pilot.press("enter")

        assert ui.state.current_actor is not None
        assert "move" in ActionService.get_available_actions(ui.state.current_actor)

        # Actor turn -> move
        new_pos = Position(x=actor.pos.x, y=actor.pos.y + 1, direction="S")
        assert actor.name in input_widget.placeholder
        input_widget.value = DecisionResult(
            action_id="move", target_position=new_pos, description="Move"
        ).model_dump_json()
        await pilot.press("enter")

        # No more resources, turns is automatically passed to next char
        assert ui.state.current_actor is not None
        assert ui.state.current_actor.name == target.name

        # No changes due to serialization
        assert len(ui.state.characters[actor.id].special_abilities) == num_abilities
        assert len(ui.state.characters[actor.id].passives) == num_passives
