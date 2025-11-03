from textual.app import ComposeResult
from textual.widgets import Static, TabbedContent, TabPane

from agent.models.state import State
from agent.ui.widgets.character_sheet import CharacterSheet


class CharacterPanel(Static):
    """Display tabs for character sheets."""

    def compose(self) -> ComposeResult:
        yield TabbedContent(id="character-tabs")

    def update_state(self, state: State) -> None:
        """Rebuild tabs and character sheets given the current state."""
        tabbed = self.query_one(TabbedContent)

        existing_ids = {pane.id for pane in tabbed.query(TabPane)}
        current_ids = set(state.characters.keys())

        # Remove tabs for missing characters
        for pane_id in existing_ids - current_ids:
            pane = tabbed.query_one(f"#{pane_id}", TabPane)
            pane.remove()

        # Add or update character panes
        for cid, char in state.characters.items():
            if cid not in existing_ids:
                # Create a new tab for this character
                tabbed.add_pane(TabPane(char.name, CharacterSheet(char), id=cid, name=char.name))
            else:
                # Update the existing sheet
                sheet = tabbed.query_one(f"#{cid} CharacterSheet", CharacterSheet)
                sheet.update_character(char)

        # Switch to the current actor if available
        if state.current_actor:
            tabbed.active = state.current_actor.id
