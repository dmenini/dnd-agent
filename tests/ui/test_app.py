import pytest
from textual.widgets import Input

from agent.character.character import Character
from agent.models.config import AgentConfig, Config
from agent.models.decision import DecisionResult
from agent.models.map import GameMap
from agent.models.position import Position
from agent.models.state import State
from agent.ui.game_ui import GameUI
from agent.ui.log_panel import LogPanel


@pytest.mark.asyncio
async def test_app(  # noqa: PLR0915
    config: AgentConfig,
    actor: Character,
    target: Character,
    game_map: GameMap,
) -> None:
    target.attributes.hp = 1

    state = State(
        map=game_map,
        characters={actor.id: actor, target.id: target},
        parties={actor.party.id: actor.party, target.party.id: target.party},
        turn_order=[actor.id, target.id],
    )
    config.decision_node["mock_llm"] = True  # To always wait and pass turn

    num_passives = len(actor.passives)
    num_abilities = len(actor.abilities)

    ui = GameUI(initial_state=state, config=Config(agent=config))
    async with ui.run_test() as pilot:
        log_panel = pilot.app.query_one("#logs", LogPanel)
        input_widget = pilot.app.query_one("#user-input", Input)
        assert input_widget.placeholder == "Press ENTER to start game..."

        # Game starts and interrupt stops execution at player's decision time
        await pilot.click(input_widget)
        await pilot.press("enter")
        await pilot.pause()

        # Actor turn -> wait
        assert actor.name in input_widget.placeholder
        assert ui.state.current_actor is not None
        assert ui.state.current_actor.id == actor.id
        assert log_panel._filtered_logs[-1].message == f"Turn 1.1 - {actor.name}"
        assert ui.state.log.events[-1].message == f"Turn 1.1 - {actor.name}"
        # No changes due to serialization
        assert len(ui.state.characters[actor.id].abilities) == num_abilities
        assert len(ui.state.characters[actor.id].passives) == num_passives

        await pilot.click(input_widget)
        input_widget.value = "wait"
        await pilot.press("enter")
        await pilot.pause()

        # Enemy turn -> waits automatically
        assert "Enemy" in input_widget.placeholder
        assert ui.state.current_actor is not None
        assert ui.state.current_actor.id == target.id
        assert log_panel._filtered_logs[-1].message == f"Turn 1.2 - {target.name}"
        assert ui.state.log.events[-1].message == f"Turn 1.2 - {target.name}"
        await pilot.click(input_widget)
        await pilot.press("enter")
        await pilot.pause()

        # Actor turn -> Attack enemy and kills
        assert actor.name in input_widget.placeholder
        assert ui.state.current_actor is not None
        assert ui.state.current_actor.id == actor.id
        assert log_panel._filtered_logs[-1].message == f"Turn 2.1 - {actor.name}"
        assert ui.state.log.events[-1].message == f"Turn 2.1 - {actor.name}"
        await pilot.click(input_widget)
        input_widget.value = DecisionResult(
            action_id="main_hand_attack", target_hits={target.id: 1}, description="Main attack"
        ).model_dump_json()
        await pilot.press("enter")
        await pilot.pause()

        # Enemy turn skipped as it's dead
        assert "Press ENTER to start new game..." in input_widget.placeholder
        assert ui.state.current_actor is not None
        assert ui.state.current_actor.id == actor.id
        assert ui.state.log.events[-1].message == "The players are victorious! Party 'Heroes' stands triumphant!"
        assert ui.state.done is True

        # Game starts again upon ENTER
        await pilot.click(input_widget)
        await pilot.press("enter")
        await pilot.pause()

        # Actor turn -> wait
        assert actor.name in input_widget.placeholder
        assert ui.state.current_actor is not None
        assert ui.state.current_actor.id == actor.id
        assert log_panel._filtered_logs[-1].message == f"Turn 1.1 - {actor.name}"
        assert ui.state.log.events[-1].message == f"Turn 1.1 - {actor.name}"
        await pilot.click(input_widget)
        input_widget.value = "wait"
        await pilot.press("enter")
        await pilot.pause()


@pytest.mark.asyncio
async def test_action_resources_are_used(
    config: AgentConfig,
    actor: Character,
    target: Character,
    game_map: GameMap,
) -> None:
    state = State(
        map=game_map,
        characters={actor.id: actor, target.id: target},
        parties={actor.party.id: actor.party, target.party.id: target.party},
        turn_order=[actor.id, target.id],
    )
    config.decision_node["mock_llm"] = True  # To always wait and pass turn

    ui = GameUI(initial_state=state, config=Config(agent=config))
    async with ui.run_test() as pilot:
        input_widget = pilot.app.query_one("#user-input", Input)
        assert input_widget.placeholder == "Press ENTER to start game..."

        # Game starts and interrupt stops execution at player's decision time
        await pilot.click(input_widget)
        await pilot.press("enter")
        await pilot.pause()

        # Actor turn -> attack
        assert actor.name in input_widget.placeholder
        await pilot.click(input_widget)
        input_widget.value = DecisionResult(
            action_id="main_hand_attack", target_hits={target.id: 1}, description="Main attack"
        ).model_dump_json()
        await pilot.press("enter")
        await pilot.pause()

        assert ui.state.current_actor is not None
        assert "main_hand_attack" not in ui.state.current_actor.get_available_actions()

        # Actor turn -> second wind (due to serialization it may be restored)
        assert actor.name in input_widget.placeholder
        await pilot.click(input_widget)
        input_widget.value = DecisionResult(action_id="second_wind", description="Second wind").model_dump_json()
        await pilot.press("enter")
        await pilot.pause()

        assert ui.state.current_actor is not None
        assert "second_wind" not in ui.state.current_actor.get_available_actions()

        # Actor turn -> turn around is free
        new_pos = Position(x=actor.pos.x, y=actor.pos.y, direction="S")
        assert actor.name in input_widget.placeholder
        await pilot.click(input_widget)
        input_widget.value = DecisionResult(
            action_id="move", target_position=new_pos, description="Second wind"
        ).model_dump_json()
        await pilot.press("enter")
        await pilot.pause()

        assert ui.state.current_actor is not None
        assert "move" in ui.state.current_actor.get_available_actions()

        # Actor turn -> move
        new_pos = Position(x=actor.pos.x, y=actor.pos.y + 1, direction="S")
        assert actor.name in input_widget.placeholder
        await pilot.click(input_widget)
        input_widget.value = DecisionResult(
            action_id="move", target_position=new_pos, description="Second wind"
        ).model_dump_json()
        await pilot.press("enter")
        await pilot.pause()

        # No more resources, turns is automatically passed to next char
        assert ui.state.current_actor is not None
        assert ui.state.current_actor.name == target.name
