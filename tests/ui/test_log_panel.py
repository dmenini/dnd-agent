from collections.abc import Iterator

import pytest
from textual.app import App

from agent.logs.events import LogEvent, LogLevel
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


# Simplified tests - access panel and pilot within the test


@pytest.mark.asyncio
async def test_initialization() -> None:
    """Test that LogPanel initializes with correct default values."""
    app = TestApp()
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
async def test_update_state_adds_new_logs(mock_state: State) -> None:
    """Test that update_state adds new logs to cached logs."""
    app = TestApp()
    async with app.run_test():
        panel = app.query_one(LogPanel)
        panel.update_state(mock_state)

        assert len(panel._cached_logs) == 7
        assert len(panel._filtered_logs) == 4  # Only top-level items initially


@pytest.mark.asyncio
async def test_press_v_key_changes_verbosity(mock_state: State) -> None:
    """Test that pressing 'v' key cycles through verbosity levels."""
    app = TestApp()
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
async def test_press_space_key_expands_item(mock_state: State) -> None:
    """Test that pressing space key expands/collapses items."""
    app = TestApp()
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
async def test_press_enter_key_expands_item(mock_state: State) -> None:
    """Test that pressing enter key expands/collapses items."""
    app = TestApp()
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
async def test_expansion_with_keyboard_navigation(mock_state: State) -> None:
    """Test expanding items while navigating with arrow keys."""
    app = TestApp()
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
async def test_verbosity_change_with_expanded_items(mock_state: State) -> None:
    """Test that verbosity changes work correctly with expanded items."""
    app = TestApp()
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
async def test_filter_logs_without_expansion(sample_logs: list[LogEvent]) -> None:
    """Test that filter_logs only shows top-level items when nothing is expanded."""
    app = TestApp()
    async with app.run_test():
        panel = app.query_one(LogPanel)
        panel._cached_logs = sample_logs
        filtered = panel._filter_logs()

        assert len(filtered) == 4
        assert all(e.type in {LogLevel.MAIN, LogLevel.SYSTEM, LogLevel.HEADER} for e in filtered)


@pytest.mark.asyncio
async def test_filter_logs_with_expansion(sample_logs: list[LogEvent]) -> None:
    """Test that filter_logs shows children when parent is expanded."""
    app = TestApp()
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
async def test_filter_logs_with_expansion_verbose(sample_logs: list[LogEvent]) -> None:
    """Test that filter_logs shows all children including DEBUG when verbose."""
    app = TestApp()
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
async def test_multiple_expansions(mock_state: State) -> None:
    """Test expanding multiple main items simultaneously."""
    app = TestApp()
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
async def test_cache_size_limit() -> None:
    """Test that cached logs are limited to CACHE_SIZE."""
    app = TestApp()
    async with app.run_test():
        panel = app.query_one(LogPanel)

        many_logs = [LogEvent(id=f"log{i}", type=LogLevel.MAIN, message=f"Log {i}") for i in range(CACHE_SIZE + 100)]

        state = State()
        state.log.events = many_logs
        panel.update_state(state)

        assert len(panel._cached_logs) == CACHE_SIZE


@pytest.mark.asyncio
async def test_incremental_append_optimization(sample_logs: list[LogEvent]) -> None:
    """Test that new logs are appended incrementally when expansion state unchanged."""
    app = TestApp()
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
async def test_toggle_expand_with_child_item(mock_state: State) -> None:
    """Test toggling expansion when selecting a child item."""
    app = TestApp()
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
async def test_rapid_key_presses(mock_state: State) -> None:
    """Test handling rapid key presses."""
    app = TestApp()
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
async def test_expansion_state_preserved_across_updates(sample_logs: list[LogEvent]) -> None:
    """Test that expansion state is preserved when new logs arrive."""
    app = TestApp()
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
async def test_update_state_incremental(sample_logs: list[LogEvent]) -> None:
    """Test that update_state only processes new logs on subsequent calls."""
    app = TestApp()
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
async def test_update_state_no_new_logs(mock_state: State) -> None:
    """Test that update_state skips processing when no new logs."""
    app = TestApp()
    async with app.run_test():
        panel = app.query_one(LogPanel)

        panel.update_state(mock_state)
        initial_count = len(panel._filtered_logs)

        # Call again with same state
        panel.update_state(mock_state)

        # Should not process anything
        assert len(panel._filtered_logs) == initial_count
