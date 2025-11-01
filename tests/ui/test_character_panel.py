from collections.abc import Iterator

import pytest
from textual.app import App
from textual.widgets import ContentSwitcher, Markdown, Tab, Tabs

from agent.character.character import Character
from agent.models.state import State
from agent.ui.character_panel import CharacterPanel, CharacterSheet


class TestApp(App):
    """Test application for LogPanel."""

    def compose(self) -> Iterator[CharacterPanel]:
        yield CharacterPanel()


@pytest.fixture
def app() -> App:
    return TestApp()


@pytest.mark.asyncio
async def test_initial_compose(app: App) -> None:
    """Test that panel composes with Tabs and ContentSwitcher."""

    async with app.run_test():
        panel = CharacterPanel()
        await app.mount(panel)

        # Check that tabs and switcher exist
        tabs = panel.query_one("#character-tabs")
        switcher = panel.query_one("#character-switcher")

        assert tabs is not None
        assert switcher is not None


@pytest.mark.asyncio
async def test_add_new_character(app: App, actor: Character) -> None:
    """Test adding a new character creates tab and sheet."""

    async with app.run_test() as pilot:
        panel = CharacterPanel()
        await app.mount(panel)

        # Create state with one character
        state = State(
            map=None,
            characters={actor.id: actor},
            parties={actor.party.id: actor.party},
            turn_order=[actor.id],
        )

        panel.update_state(state)
        await pilot.pause()

        # Verify tab was created
        tabs = panel.query_one("#character-tabs")
        tab = tabs.query_one(f"#{actor.id}", Tab)
        assert tab is not None
        assert tab.label.plain == actor.name

        # Verify sheet was created
        switcher = panel.query_one("#character-switcher")
        sheet = switcher.query_one(f"#{actor.id}")
        assert sheet is not None


@pytest.mark.asyncio
async def test_add_multiple_characters(app: App, actor: Character, target: Character) -> None:
    """Test adding multiple characters."""

    async with app.run_test() as pilot:
        panel = CharacterPanel()
        await app.mount(panel)

        state = State(
            map=None,
            characters={actor.id: actor, target.id: target},
            parties={actor.party.id: actor.party, target.party.id: target.party},
            turn_order=[actor.id, target.id],
        )

        panel.update_state(state)
        await pilot.pause()

        tabs = panel.query_one("#character-tabs")
        assert len(tabs.query("Tab")) == 2

        switcher = panel.query_one("#character-switcher")
        assert len(switcher.query("CharacterSheet")) == 2


@pytest.mark.asyncio
async def test_update_existing_character(app: App, actor: Character) -> None:
    async with app.run_test() as pilot:
        panel = CharacterPanel()
        await app.mount(panel)

        # Add initial character
        state1 = State(
            characters={actor.id: actor},
            parties={actor.party.id: actor.party},
            turn_order=[actor.id],
        )
        panel.update_state(state1)
        await pilot.pause()

        # Get reference to original sheet
        switcher = panel.query_one("#character-switcher")
        original_sheet = switcher.query_one(f"#{actor.id}", CharacterSheet)

        # Update character with same ID
        actor_updated = actor.model_copy(deep=True)
        actor_updated.name = "Artur updated"
        state2 = State(
            map=None,
            characters={actor.id: actor_updated},
            parties={actor.party.id: actor.party},
            turn_order=[actor.id],
        )
        panel.update_state(state2)
        await pilot.pause()

        # Verify same sheet instance (not recreated)
        updated_sheet = switcher.query_one(f"#{actor.id}", CharacterSheet)
        assert updated_sheet is original_sheet

        # Verify update_character was called
        assert updated_sheet.char is not None
        assert updated_sheet.char.name == actor_updated.name


@pytest.mark.asyncio
async def test_remove_character(app: App, actor: Character, target: Character) -> None:
    """Test removing a character removes tab and sheet."""

    async with app.run_test() as pilot:
        panel = CharacterPanel()
        await app.mount(panel)

        # Add two characters
        state1 = State(
            characters={actor.id: actor, target.id: target},
            parties={actor.party.id: actor.party, target.party.id: target.party},
            turn_order=[actor.id, target.id],
        )
        panel.update_state(state1)
        await pilot.pause()

        # Remove one character
        state2 = State(
            characters={actor.id: actor},
            parties={actor.party.id: actor.party},
            turn_order=[actor.id],
        )
        panel.update_state(state2)
        await pilot.pause()

        # Verify char1 tab and sheet are gone
        tabs = panel.query_one("#character-tabs")
        assert len(tabs.query(f"#{target.id}")) == 0

        switcher = panel.query_one("#character-switcher")
        assert len(switcher.query(f"#{target.id}")) == 0

        # Verify char2 is still there
        assert len(tabs.query(f"#{actor.id}")) == 1
        assert len(switcher.query(f"#{actor.id}")) == 1


@pytest.mark.asyncio
async def test_remove_all_characters(app: App, actor: Character) -> None:
    """Test removing all characters."""

    async with app.run_test() as pilot:
        panel = CharacterPanel()
        await app.mount(panel)

        # Add characters
        state1 = State(
            characters={actor.id: actor},
            parties={actor.party.id: actor.party},
            turn_order=[actor.id],
        )
        panel.update_state(state1)
        await pilot.pause()

        # Remove all
        state2 = State(
            characters={},
            parties={},
            turn_order=[],
        )
        panel.update_state(state2)
        await pilot.pause()

        tabs = panel.query_one("#character-tabs")
        switcher = panel.query_one("#character-switcher")

        assert len(tabs.query("Tab")) == 0
        assert len(switcher.query("CharacterSheet")) == 0


@pytest.mark.asyncio
async def test_set_active_tab_with_turn_order(app: App, actor: Character, target: Character) -> None:
    """Test that active tab is set based on current actor."""

    async with app.run_test() as pilot:
        panel = CharacterPanel()
        await app.mount(panel)

        state = State(
            characters={actor.id: actor, target.id: target},
            parties={actor.party.id: actor.party, target.party.id: target.party},
            turn_order=[actor.id, target.id],
            turn_index=1,
        )

        panel.update_state(state)
        await pilot.pause()

        tabs = panel.query_one("#character-tabs", Tabs)
        switcher = panel.query_one("#character-switcher", ContentSwitcher)

        assert tabs.active == actor.id
        assert switcher.current == actor.id


@pytest.mark.asyncio
async def test_no_turn_order_doesnt_change_active(app: App, actor: Character) -> None:
    """Test that without turn_order, active tab isn't changed."""

    async with app.run_test() as pilot:
        panel = CharacterPanel()
        await app.mount(panel)

        state = State(
            characters={actor.id: actor},
            parties={actor.party.id: actor.party},
        )

        panel.update_state(state)
        await pilot.pause()

        # Should not crash, tabs/switcher should have default state
        tabs = panel.query_one("#character-tabs")
        # Just verify no exception occurred
        assert tabs is not None


@pytest.mark.asyncio
async def test_mixed_add_update_remove(app: App, actor: Character, target: Character) -> None:
    """Test adding, updating, and removing characters in one update."""

    async with app.run_test() as pilot:
        panel = CharacterPanel()
        await app.mount(panel)

        # Initial state
        state1 = State(
            characters={actor.id: actor, target.id: target},
            parties={actor.party.id: actor.party, target.party.id: target.party},
            turn_order=[actor.id, target.id],
            turn_index=0,
        )
        panel.update_state(state1)
        await pilot.pause()

        # Mixed update: remove char1, update char2, add char3
        actor_new = actor.model_copy(deep=True)
        actor_new.name = "Artur new"
        actor_new.id = "new"

        actor_updated = actor.model_copy(deep=True)
        actor_updated.name = "Artur updated"
        state2 = State(
            characters={actor_new.id: actor_new, actor_updated.id: actor_updated},
            parties={actor_new.party.id: actor_new.party, actor_updated.party.id: actor_updated.party},
            turn_order=[actor_new.id, actor_updated.id],
            turn_index=0,
        )
        panel.update_state(state2)
        await pilot.pause()

        tabs = panel.query_one("#character-tabs")
        switcher = panel.query_one("#character-switcher")

        # char1 removed
        assert len(tabs.query(f"#{target.id}")) == 0
        assert len(switcher.query(f"#{target.id}")) == 0

        # char2 updated (still exists)
        assert len(tabs.query(f"#{actor.id}")) == 1
        sheet2 = switcher.query_one(f"#{actor.id}", CharacterSheet)
        assert sheet2.char is not None
        assert sheet2.char.name == actor_updated.name

        # char3 added
        assert len(tabs.query(f"#{actor_new.id}")) == 1
        assert len(switcher.query(f"#{actor_new.id}")) == 1


@pytest.mark.asyncio
async def test_update_character_updates_content(app: App, actor: Character) -> None:
    """Test that update_character refreshes the sheet content."""
    async with app.run_test() as pilot:
        sheet = CharacterSheet(actor)
        await app.mount(sheet)

        # Update character
        actor_updated = actor.model_copy(deep=True)
        actor_updated.name = "Artur updated"
        sheet.update_character(actor_updated)
        await pilot.pause()

        # Verify the character reference was updated
        assert sheet.char is not None
        assert sheet.char.name == actor_updated.name

        # Verify markdown was updated
        header = sheet.query_one(Markdown)
        assert actor_updated.name in str(header.children[0].content)
