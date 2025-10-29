import pytest
from textual.app import App

from agent.logs.events import LogEvent, LogLevel
from agent.models.state import State
from agent.ui.log_panel import LogPanel


def make_state() -> State:
    logs = [
        LogEvent(id="h1", type=LogLevel.HEADER, message="Header 1"),
        LogEvent(id="m1", type=LogLevel.MAIN, message="Main 1"),
        LogEvent(id="d1", type=LogLevel.DETAIL, message="Detail A"),
        LogEvent(id="m2", type=LogLevel.MAIN, message="Main 2"),
        LogEvent(id="dbg1", type=LogLevel.DEBUG, message="Debug X"),
        LogEvent(id="d2", type=LogLevel.DETAIL, message="Detail B"),
    ]
    return type("FakeState", (), {"log": type("L", (), {"events": logs})()})()


class LogPanelTestApp(App):
    async def on_mount(self) -> None:
        self.panel = LogPanel()
        await self.mount(self.panel)


@pytest.fixture
def test_app() -> App:
    return LogPanelTestApp()


@pytest.mark.asyncio
async def test_up_down(test_app: LogPanelTestApp) -> None:
    async with test_app.run_test() as pilot:
        app = pilot.app
        panel = app.panel

        # Initialize state and update logs
        state = make_state()
        panel.update_state(state)
        await pilot.pause()
        assert len(panel._cached_logs) == len(state.log.events)
        assert len(panel._filtered_logs) == 3
        assert panel._selectable_indices == [1, 2]
        assert panel.selected_index == 1
        assert panel._filtered_logs[panel._selectable_indices[panel.selected_index]].id == "m2"

        # Move selection down -> doesn't move
        await pilot.press("down")
        await pilot.pause()
        assert panel.selected_index == 1
        assert panel._filtered_logs[panel._selectable_indices[panel.selected_index]].id == "m2"

        # Move selection up
        await pilot.press("up")
        await pilot.pause()
        assert panel.selected_index == 0
        assert panel._filtered_logs[panel._selectable_indices[panel.selected_index]].id == "m1"

        # Move selection up -> doesn't move
        await pilot.press("up")
        await pilot.pause()
        assert panel.selected_index == 0
        assert panel._filtered_logs[panel._selectable_indices[panel.selected_index]].id == "m1"

        # Move selection down
        await pilot.press("down")
        await pilot.pause()
        assert panel.selected_index == 1
        assert panel._filtered_logs[panel._selectable_indices[panel.selected_index]].id == "m2"


@pytest.mark.asyncio
async def test_selection_and_expansion_last_main(test_app: LogPanelTestApp) -> None:
    async with test_app.run_test() as pilot:
        app = pilot.app
        panel = app.panel

        # Initialize state and update logs
        state = make_state()
        panel.update_state(state)
        await pilot.pause()
        assert panel.selected_index == 1
        assert len(panel._cached_logs) == len(state.log.events)
        assert len(panel._filtered_logs) == 3
        assert panel._selectable_indices == [1, 2]

        # Expand first MAIN log
        await pilot.press("enter")
        await pilot.pause()

        # DETAIL/DEBUG logs should now appear
        assert panel._selectable_indices == [1, 2, 3, 4]
        assert len(panel._filtered_logs) == 5
        assert any(e.type in {LogLevel.DETAIL, LogLevel.DEBUG} for e in panel._filtered_logs)

        # Collapse again
        await pilot.press("enter")
        await pilot.pause()
        assert len(panel._filtered_logs) == 3
        assert not any(e.type in {LogLevel.DETAIL, LogLevel.DEBUG} for e in panel._filtered_logs)


@pytest.mark.asyncio
async def test_selection_and_expansion_first_main(test_app: LogPanelTestApp) -> None:
    async with test_app.run_test() as pilot:
        app = pilot.app
        panel = app.panel

        # Initialize state and update logs
        state = make_state()
        panel.update_state(state)
        await pilot.pause()
        assert panel.selected_index == 1
        assert len(panel._cached_logs) == len(state.log.events)
        assert len(panel._filtered_logs) == 3
        assert panel._selectable_indices == [1, 2]

        # Move selection down
        await pilot.press("up")
        await pilot.pause()
        assert panel.selected_index == 0

        # Expand first MAIN log
        await pilot.press("enter")
        await pilot.pause()

        # DETAIL/DEBUG logs should now appear
        assert panel._selectable_indices == [1, 2, 3]
        assert len(panel._filtered_logs) == 4
        assert any(e.type in {LogLevel.DETAIL, LogLevel.DEBUG} for e in panel._filtered_logs)

        # Go into the DETAIL section
        await pilot.press("down")
        await pilot.pause()
        assert panel.selected_index == 1
        assert panel._filtered_logs[panel._selectable_indices[panel.selected_index]].id == "d1"

        # Collapse again
        await pilot.press("enter")
        await pilot.pause()
        assert len(panel._filtered_logs) == 3
        assert not any(e.type in {LogLevel.DETAIL, LogLevel.DEBUG} for e in panel._filtered_logs)

        assert panel.selected_index == 0
        assert panel._selectable_indices == [1, 2]
