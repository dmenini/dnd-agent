from typing import Any

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widgets import Markdown, Static

from agent.character.character import Character
from agent.ui.widgets.action_table import ActionsSummaryTable


class CharacterSheet(Static):
    """Character sheet that reactively updates when character changes."""

    char: reactive[Character | None] = reactive(default=None, init=False)

    def __init__(self, char: Character, **kwargs: Any) -> None:
        super().__init__(id=char.id, **kwargs)
        self.char = char

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Markdown(id="char-header")
            yield Markdown("# Available Actions", id="actions-header")
            yield ActionsSummaryTable(id="actions-table")

    def on_mount(self) -> None:
        """Initialize content after mounting."""
        self._update_content()

    def watch_char(self) -> None:
        """Called automatically when char changes."""
        if self.is_mounted:
            self._update_content()

    def _update_content(self) -> None:
        """Update all child widgets with current character data."""
        if not self.char:
            return

        # Update the character header
        header = self.query_one("#char-header", Markdown)
        header.update(f"# Character {self.char}\n")

        # Update the actions table
        actions_table = self.query_one("#actions-table", ActionsSummaryTable)
        actions = list(self.char.get_available_actions().values())
        actions_table.update_actions(actions)

    def update_character(self, char: Character) -> None:
        """Update the sheet with new character data."""
        self.char = char  # This automatically triggers watch_char
