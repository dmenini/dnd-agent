from collections.abc import Iterator

import pytest
from textual.app import App

from agent.logs.log_event import LogEvent, LogLevel
from agent.models.state import State
from agent.ui.log_panel import CACHE_SIZE, LogPanel


@pytest.fixture
def sample_logs() -> list[LogEvent]:
    """Create a sample set of log events."""
    return [
        LogEvent(id="main1", type=LogLevel.MAIN, message="Main event 1"),
        LogEvent(id="detail1", type=LogLevel.DETAIL, message="Detail 1"),
        LogEvent(id="debug1", type=LogLevel.DEBUG, message="Debug 1"),
        LogEvent(id="main2", type=LogLevel.MAIN, message="Main event 2"),
        LogEvent(id="detail2", type=LogLevel.DETAIL, message="Detail 2"),
        LogEvent(id="system1", type=LogLevel.SYSTEM, message="System event"),
        LogEvent(id="header1", type=LogLevel.HEADER, message="Header event"),
    ]


@pytest.fixture
def mock_state(sample_logs: list[LogEvent]) -> State:
    """Create a mock State with log events."""
    state = State()
    state.log.events = sample_logs
    return state


class TestApp(App):
    """Test application for LogPanel."""

    def compose(self) -> Iterator[LogPanel]:
        yield LogPanel()


@pytest.fixture
def app() -> App:
    return TestApp()


@pytest.mark.asyncio
async def test_initialization(app: App) -> None:
    """Test that LogPanel initializes with correct default values."""
    async with app.run_test():
        panel = app.query_one(LogPanel)

        assert panel.verbosity == 1
        assert panel._cached_logs == []
        assert panel._expanded_mains == set()
        assert panel._main_lookup == {}
        assert panel._filtered_logs == []
        assert panel._last_rendered_count == 0
        assert panel._was_at_bottom is True
        assert panel._last_verbosity == 1


@pytest.mark.asyncio
async def test_update_state_adds_new_logs(app: App, mock_state: State) -> None:
    """Test that update_state adds new logs to cached logs."""
    async with app.run_test():
        panel = app.query_one(LogPanel)
        panel.update_state(mock_state)

        assert len(panel._cached_logs) == 7
        assert len(panel._filtered_logs) == 4  # Only top-level items initially


@pytest.mark.asyncio
async def test_press_v_key_changes_verbosity(app: App, mock_state: State) -> None:
    """Test that pressing 'v' key cycles through verbosity levels."""
    async with app.run_test() as pilot:
        panel = app.query_one(LogPanel)
        panel.update_state(mock_state)

        # Expand all MAIN items to see their children
        panel._expanded_mains = {log.id for log in mock_state.log.events if log.type == LogLevel.MAIN}
        panel.refresh_logs()

        # Verbosity 1 (Normal): shows MAIN, SYSTEM, HEADER, DETAIL (no DEBUG)
        assert panel.verbosity == 1
        assert len(panel._filtered_logs) == 6  # main1, detail1, main2, detail2, system1, header1

        # Press 'v' to cycle to verbose (2) - adds DEBUG logs
        await pilot.press("v")
        assert panel.verbosity == 2
        assert len(panel._filtered_logs) == 7  # + debug1

        # Press 'v' to cycle to minimal (0) - only MAIN, SYSTEM, HEADER
        await pilot.press("v")
        assert panel.verbosity == 0
        assert len(panel._filtered_logs) == 4  # main1, main2, system1, header1

        # Press 'v' to cycle back to normal (1)
        await pilot.press("v")
        assert panel.verbosity == 1
        assert len(panel._filtered_logs) == 6  # back to MAIN, DETAIL, SYSTEM, HEADER


@pytest.mark.asyncio
async def test_press_space_key_expands_item(app: App, mock_state: State) -> None:
    """Test that pressing space key expands/collapses items."""
    async with app.run_test() as pilot:
        panel = app.query_one(LogPanel)
        panel.update_state(mock_state)
        panel.focus()
        panel.index = 0

        initial_count = len(panel._filtered_logs)

        # Press space to expand
        await pilot.press("space")
        assert "main1" in panel._expanded_mains
        assert len(panel._filtered_logs) > initial_count

        # Press space again to collapse
        panel.index = 0
        await pilot.press("space")
        assert "main1" not in panel._expanded_mains


@pytest.mark.asyncio
async def test_press_enter_key_expands_item(app: App, mock_state: State) -> None:
    """Test that pressing enter key expands/collapses items."""
    async with app.run_test() as pilot:
        panel = app.query_one(LogPanel)
        panel.update_state(mock_state)
        panel.focus()
        panel.index = 0

        # Press enter to expand
        await pilot.press("enter")
        assert "main1" in panel._expanded_mains

        # Press enter again to collapse
        panel.index = 0
        await pilot.press("enter")
        assert "main1" not in panel._expanded_mains


@pytest.mark.asyncio
async def test_expansion_with_keyboard_navigation(app: App, mock_state: State) -> None:
    """Test expanding items while navigating with arrow keys."""
    async with app.run_test() as pilot:
        panel = app.query_one(LogPanel)
        panel.update_state(mock_state)
        panel.focus()

        # Navigate to first item and expand
        panel.index = 0
        await pilot.press("space")
        assert "main1" in panel._expanded_mains

        # Navigate down through expanded items
        await pilot.press("down")
        assert panel.index == 1  # Should be on detail1

        # Navigate to main2 and expand it
        main2_idx = next(i for i, e in enumerate(panel._filtered_logs) if e.id == "main2")
        panel.index = main2_idx
        await pilot.press("space")
        assert "main2" in panel._expanded_mains


@pytest.mark.asyncio
async def test_verbosity_change_with_expanded_items(app: App, mock_state: State) -> None:
    """Test that verbosity changes work correctly with expanded items."""
    async with app.run_test() as pilot:
        panel = app.query_one(LogPanel)
        panel.update_state(mock_state)
        panel.focus()

        # Expand main1
        panel.index = 0
        await pilot.press("space")
        expanded_count = len(panel._filtered_logs)

        # Change to minimal verbosity - should hide details even when expanded
        await pilot.press("v")  # to 2
        await pilot.press("v")  # to 0
        assert panel.verbosity == 0
        assert len(panel._filtered_logs) < expanded_count

        # Back to normal - details should reappear since still expanded
        await pilot.press("v")  # to 1
        assert len(panel._filtered_logs) > 4  # More than just top-level


@pytest.mark.asyncio
async def test_filter_logs_without_expansion(app: App, sample_logs: list[LogEvent]) -> None:
    """Test that filter_logs only shows top-level items when nothing is expanded."""
    async with app.run_test():
        panel = app.query_one(LogPanel)
        panel._cached_logs = sample_logs
        filtered = panel._filter_logs()

        assert len(filtered) == 4
        assert all(e.type in {LogLevel.MAIN, LogLevel.SYSTEM, LogLevel.HEADER} for e in filtered)


@pytest.mark.asyncio
async def test_filter_logs_with_expansion(app: App, sample_logs: list[LogEvent]) -> None:
    """Test that filter_logs shows children when parent is expanded."""
    async with app.run_test():
        panel = app.query_one(LogPanel)
        panel._cached_logs = sample_logs
        panel._expanded_mains.add("main1")
        filtered = panel._filter_logs()

        # With verbosity 1 (default), DEBUG is excluded
        # Should show: main1, detail1, main2, system1, header1
        assert len(filtered) == 5
        assert filtered[0].id == "main1"
        assert filtered[1].id == "detail1"
        # debug1 is NOT shown because verbosity is 1
        assert filtered[2].id == "main2"


@pytest.mark.asyncio
async def test_filter_logs_with_expansion_verbose(app: App, sample_logs: list[LogEvent]) -> None:
    """Test that filter_logs shows all children including DEBUG when verbose."""
    async with app.run_test():
        panel = app.query_one(LogPanel)
        panel.verbosity = 2  # Set to verbose to include DEBUG
        panel._cached_logs = sample_logs
        panel._expanded_mains.add("main1")
        filtered = panel._filter_logs()

        # With verbosity 2, DEBUG is included
        assert len(filtered) == 6
        assert filtered[0].id == "main1"
        assert filtered[1].id == "detail1"
        assert filtered[2].id == "debug1"
        assert filtered[3].id == "main2"


@pytest.mark.asyncio
async def test_multiple_expansions(app: App, mock_state: State) -> None:
    """Test expanding multiple main items simultaneously."""
    async with app.run_test() as pilot:
        panel = app.query_one(LogPanel)
        panel.update_state(mock_state)
        panel.focus()

        # Expand main1
        panel.index = 0
        await pilot.press("space")

        # Find and expand main2
        main2_idx = next(i for i, e in enumerate(panel._filtered_logs) if e.id == "main2")
        panel.index = main2_idx
        await pilot.press("space")

        assert "main1" in panel._expanded_mains
        assert "main2" in panel._expanded_mains


@pytest.mark.asyncio
async def test_cache_size_limit(app: App) -> None:
    """Test that cached logs are limited to CACHE_SIZE."""
    async with app.run_test():
        panel = app.query_one(LogPanel)

        many_logs = [LogEvent(id=f"log{i}", type=LogLevel.MAIN, message=f"Log {i}") for i in range(CACHE_SIZE + 100)]

        state = State()
        state.log.events = many_logs
        panel.update_state(state)

        assert len(panel._cached_logs) == CACHE_SIZE


@pytest.mark.asyncio
async def test_incremental_append_optimization(app: App, sample_logs: list[LogEvent]) -> None:
    """Test that new logs are appended incrementally when expansion state unchanged."""
    async with app.run_test():
        panel = app.query_one(LogPanel)

        state1 = State()
        state1.log.events = sample_logs[:3]
        panel.update_state(state1)
        initial_count = len(panel._filtered_logs)

        state2 = State()
        state2.log.events = sample_logs
        panel.update_state(state2)

        assert len(panel._filtered_logs) > initial_count


@pytest.mark.asyncio
async def test_toggle_expand_with_child_item(app: App, mock_state: State) -> None:
    """Test toggling expansion when selecting a child item."""
    async with app.run_test() as pilot:
        panel = app.query_one(LogPanel)
        panel.update_state(mock_state)
        panel.focus()

        # Expand main1
        panel.index = 0
        await pilot.press("space")
        assert "main1" in panel._expanded_mains

        # Click on detail1 (child of main1)
        detail_idx = next(i for i, e in enumerate(panel._filtered_logs) if e.id == "detail1")
        panel.index = detail_idx
        await pilot.press("space")

        # Should collapse main1
        assert "main1" not in panel._expanded_mains


@pytest.mark.asyncio
async def test_rapid_key_presses(app: App, mock_state: State) -> None:
    """Test handling rapid key presses."""
    async with app.run_test() as pilot:
        panel = app.query_one(LogPanel)
        panel.update_state(mock_state)
        panel.focus()

        # Rapid verbosity changes
        n = 10
        for _ in range(10):
            await pilot.press("v")

        assert panel.verbosity == n % 3 + 1
        assert len(panel._filtered_logs) > 0


@pytest.mark.asyncio
async def test_expansion_state_preserved_across_updates(app: App, sample_logs: list[LogEvent]) -> None:
    """Test that expansion state is preserved when new logs arrive."""
    async with app.run_test() as pilot:
        panel = app.query_one(LogPanel)

        # Initial state with partial logs
        state1 = State()
        state1.log.events = sample_logs[:4]
        panel.update_state(state1)
        panel.focus()

        # Expand main1
        panel.index = 0
        await pilot.press("space")
        assert "main1" in panel._expanded_mains

        # Add more logs
        state2 = State()
        state2.log.events = sample_logs
        panel.update_state(state2)

        # main1 should still be expanded
        assert "main1" in panel._expanded_mains


@pytest.mark.asyncio
async def test_update_state_incremental(app: App, sample_logs: list[LogEvent]) -> None:
    """Test that update_state only processes new logs on subsequent calls."""
    async with app.run_test():
        panel = app.query_one(LogPanel)

        # First update with 3 logs
        state1 = State()
        state1.log.events = sample_logs[:3]
        panel.update_state(state1)
        assert len(panel._cached_logs) == 3

        # Second update with all 7 logs (4 new ones)
        state2 = State()
        state2.log.events = sample_logs
        panel.update_state(state2)
        assert len(panel._cached_logs) == 7
        assert panel._last_rendered_count == 7


@pytest.mark.asyncio
async def test_update_state_no_new_logs(app: App, mock_state: State) -> None:
    """Test that update_state skips processing when no new logs."""
    async with app.run_test():
        panel = app.query_one(LogPanel)

        panel.update_state(mock_state)
        initial_count = len(panel._filtered_logs)

        # Call again with same state
        panel.update_state(mock_state)

        # Should not process anything
        assert len(panel._filtered_logs) == initial_count


@pytest.mark.asyncio
async def test_items_without_children_are_disabled(app: App) -> None:
    """Test that MAIN/SYSTEM items without children are disabled."""
    async with app.run_test():
        panel = app.query_one(LogPanel)

        # Create logs where some MAIN items have children and some don't
        logs_with_mixed_children = [
            LogEvent(id="main1", type=LogLevel.MAIN, message="Main with children"),
            LogEvent(id="detail1", type=LogLevel.DETAIL, message="Detail 1"),
            LogEvent(id="main2", type=LogLevel.MAIN, message="Main without children"),
            LogEvent(id="main3", type=LogLevel.MAIN, message="Another main with children"),
            LogEvent(id="debug3", type=LogLevel.DEBUG, message="Debug 3"),
            LogEvent(id="system1", type=LogLevel.SYSTEM, message="System without children"),
            LogEvent(id="header1", type=LogLevel.HEADER, message="Header"),
        ]

        state = State()
        state.log.events = logs_with_mixed_children
        panel.update_state(state)

        # Check that items are properly disabled/enabled
        list_items = list(panel.children)

        # main1 has children -> should be enabled
        assert list_items[0].disabled is False

        # main2 has no children -> should be disabled
        assert list_items[1].disabled is True

        # main3 has children -> should be enabled
        assert list_items[2].disabled is False

        # system1 has no children -> should be disabled
        assert list_items[3].disabled is True

        # header1 -> should be disabled (headers are always disabled)
        assert list_items[4].disabled is True


@pytest.mark.asyncio
async def test_items_with_children_become_selectable(app: App) -> None:
    """Test that items with children are selectable and can be expanded."""
    async with app.run_test() as pilot:
        panel = app.query_one(LogPanel)

        logs = [
            LogEvent(id="main1", type=LogLevel.MAIN, message="Main with children"),
            LogEvent(id="detail1", type=LogLevel.DETAIL, message="Detail 1"),
            LogEvent(id="debug1", type=LogLevel.DEBUG, message="Debug 1"),
        ]

        state = State()
        state.log.events = logs
        panel.update_state(state)
        panel.focus()

        # main1 should be enabled (has children)
        list_items = list(panel.children)
        assert list_items[0].disabled is False

        # Should be able to expand it
        panel.index = 0
        await pilot.press("space")

        assert "main1" in panel._expanded_mains
        # With verbosity 1, should see main1 and detail1 (not debug1)
        assert len(panel._filtered_logs) == 2


@pytest.mark.asyncio
async def test_disabled_items_cannot_be_expanded(app: App) -> None:
    """Test that disabled items (without children) cannot be expanded."""
    async with app.run_test() as pilot:
        panel = app.query_one(LogPanel)

        logs = [
            LogEvent(id="main1", type=LogLevel.MAIN, message="Main without children"),
            LogEvent(id="main2", type=LogLevel.MAIN, message="Another main without children"),
        ]

        state = State()
        state.log.events = logs
        panel.update_state(state)
        panel.focus()

        # Both items should be disabled
        list_items = list(panel.children)
        assert list_items[0].disabled is True
        assert list_items[1].disabled is True

        # Try to expand main1
        panel.index = 0
        await pilot.press("space")

        # Should not be expanded (disabled items shouldn't respond)
        assert "main1" not in panel._expanded_mains


@pytest.mark.asyncio
async def test_child_items_are_always_enabled(app: App) -> None:
    """Test that DETAIL and DEBUG items are never disabled."""
    async with app.run_test():
        panel = app.query_one(LogPanel)
        panel.verbosity = 2  # Show all logs including DEBUG

        logs = [
            LogEvent(id="main1", type=LogLevel.MAIN, message="Main event"),
            LogEvent(id="detail1", type=LogLevel.DETAIL, message="Detail 1"),
            LogEvent(id="debug1", type=LogLevel.DEBUG, message="Debug 1"),
        ]

        state = State()
        state.log.events = logs
        panel.update_state(state)

        # Expand to show children
        panel._expanded_mains.add("main1")
        panel.refresh_logs()

        list_items = list(panel.children)

        # main1 should be enabled
        assert list_items[0].disabled is False

        # detail1 and debug1 should be enabled (child items are always enabled)
        assert list_items[1].disabled is False  # detail1
        assert list_items[2].disabled is False  # debug1


@pytest.mark.asyncio
async def test_disabled_state_updates_on_new_logs(app: App) -> None:
    """Test that disabled state is updated when new logs arrive."""
    async with app.run_test():
        panel = app.query_one(LogPanel)

        # Start with a main without children
        logs1 = [
            LogEvent(id="main1", type=LogLevel.MAIN, message="Main without children"),
        ]

        state1 = State()
        state1.log.events = logs1
        panel.update_state(state1)

        # main1 should be disabled (no children)
        list_items = list(panel.children)
        assert list_items[0].disabled is True

        # Add children to main1
        logs2 = [
            LogEvent(id="main1", type=LogLevel.MAIN, message="Main without children"),
            LogEvent(id="detail1", type=LogLevel.DETAIL, message="Detail 1"),
        ]

        state2 = State()
        state2.log.events = logs2
        panel.update_state(state2)

        # main1 should now be enabled (has children)
        list_items = list(panel.children)
        assert list_items[0].disabled is False


@pytest.mark.asyncio
async def test_system_events_without_children_are_disabled(app: App) -> None:
    """Test that SYSTEM events without children are disabled."""
    async with app.run_test():
        panel = app.query_one(LogPanel)

        logs = [
            LogEvent(id="system1", type=LogLevel.SYSTEM, message="System without children"),
            LogEvent(id="system2", type=LogLevel.SYSTEM, message="System with children"),
            LogEvent(id="detail2", type=LogLevel.DETAIL, message="Detail for system2"),
        ]

        state = State()
        state.log.events = logs
        panel.update_state(state)

        list_items = list(panel.children)

        # system1 has no children -> should be disabled
        assert list_items[0].disabled is True

        # system2 has children -> should be enabled
        assert list_items[1].disabled is False
