import pytest
from textual.widgets import Input

from agent.character.character import Character
from agent.models.config import AgentConfig, Config
from agent.models.map import GameMap
from agent.models.state import State
from agent.ui.game_ui import GameUI
from agent.ui.log_panel import LogPanel


@pytest.mark.asyncio
async def test_on_input_submitted(
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

    config = Config(agent=config)
    ui = GameUI(initial_state=state, config=config)
    async with ui.run_test() as pilot:
        input_widget = pilot.app.query_one("#user-input", Input)
        assert input_widget.placeholder == "Press ENTER to start game..."

        # Game starts and interrupt stops execution at player's decision time
        await pilot.click(input_widget)
        await pilot.press("enter")
        await pilot.pause()

        # Actor turn
        assert actor.name in input_widget.placeholder
        assert ui.state.current_actor.id == actor.id
        log_panel = pilot.app.query_one("#logs", LogPanel)
        assert "heading-turn" in log_panel.children[-1].children[0].children[0].id
        assert log_panel._filtered_logs[-1].message == f"Turn 1.1 - {actor.name}"
        assert ui.state.log.events[-1].message == f"Turn 1.1 - {actor.name}"
        await pilot.click(input_widget)
        await pilot.press("enter")
        await pilot.pause()

        # Enemy turn
        assert "Enemy" in input_widget.placeholder
        assert ui.state.current_actor.id == target.id
        log_panel = pilot.app.query_one("#logs", LogPanel)
        assert log_panel._filtered_logs[-1].message == f"Turn 1.2 - {target.name}"
        assert "heading-turn" in log_panel.children[-1].children[0].children[0].id
        assert ui.state.log.events[-1].message == f"Turn 1.2 - {target.name}"
        await pilot.click(input_widget)
        await pilot.press("enter")
        await pilot.pause()

        # Actor turn
        assert actor.name in input_widget.placeholder
        assert ui.state.current_actor.id == actor.id
        log_panel = pilot.app.query_one("#logs", LogPanel)
        assert log_panel._filtered_logs[-1].message == f"Turn 2.1 - {actor.name}"
        assert "heading-turn" in log_panel.children[-1].children[0].children[0].id
        assert ui.state.log.events[-1].message == f"Turn 2.1 - {actor.name}"
        await pilot.click(input_widget)
        await pilot.press("enter")
        await pilot.pause()

        # Enemy turn
        assert "Enemy" in input_widget.placeholder
        assert ui.state.current_actor.id == target.id
        log_panel = pilot.app.query_one("#logs", LogPanel)
        assert "heading-turn" in log_panel.children[-1].children[0].children[0].id
        assert log_panel._filtered_logs[-1].message == f"Turn 2.2 - {target.name}"
        assert ui.state.log.events[-1].message == f"Turn 2.2 - {target.name}"

        # TODO: Actor kills monster and wins
