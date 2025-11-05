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
        sheet = self.query_one("#char-header", Markdown)
        sheet.update(self.get_content(char=self.char))

        # Update the actions table
        actions_table = self.query_one("#actions-table", ActionsSummaryTable)
        actions = list(self.char.get_available_actions().values())
        actions_table.update_actions(actions)

    def update_character(self, char: Character) -> None:
        """Update the sheet with new character data."""
        self.char = char  # This automatically triggers watch_char

    def get_content(self, char: Character) -> str:
        return (
            f"# Character **{char.name} {char.icon} (ID: {char.id})**\n\n"
            f"{char.narrative.summary}\n\n"
            f"Class: {char.job.type.value} | Level: {char.level} | Party: {char.party.name}\n\n"
            f"HP: {char.attributes.hp}/{char.max_hp} | AC: {char.armor_class}\n\n"
            f"Position: ({char.pos.x}, {char.pos.y}) | Facing: {char.pos.direction} | "
            f"Movement Remaining: {char.current_speed}/{char.speed} m | Hidden: {char.is_hidden}\n\n"
            f"Status Effects: {', '.join(str(eff) for eff in char.status_effects) or 'None'}\n\n"
            f"Passives: {', '.join(eff.name for eff in char.passives) or 'None'}\n\n"
            f"Spell Slots: {char.spell_slots}\n\n"
            f"Stats: {char.attributes}"
        )
