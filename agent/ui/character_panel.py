from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.events import Key
from textual.reactive import reactive
from textual.screen import ModalScreen, ScreenResultType
from textual.widgets import ContentSwitcher, DataTable, Footer, Markdown, Static, Tab, Tabs

from agent.actions.base import Action
from agent.actions.common.attack import AttackAction
from agent.actions.common.spell import AttackSpellAction, SupportSpellAction
from agent.actions.render import render_action
from agent.character.character import Character
from agent.models.state import State


class ActionInfoModal(ModalScreen):
    """Modal showing detailed information about an action."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
    ]

    def __init__(self, action: Action, max_width: int = 60) -> None:
        super().__init__()
        self.action = action
        self.max_width = max_width

    def compose(self) -> ComposeResult:
        """Render the modal content as a card."""
        with Horizontal(id="hcenter"):
            yield Static(render_action(self.action, max_width=self.max_width), id="card")
        yield Footer()

    @on(Key)
    def action_dismiss(self, _: ScreenResultType | None = None) -> None:  # type: ignore[override]
        """Close modal on any key press."""
        self.dismiss()


class ActionsSummaryTable(DataTable):
    """A compact summary table of all actions with minimal info."""

    actions: reactive[dict[str, Action]] = reactive(dict, init=False)

    def __init__(self, actions: list[Action] | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.actions = {a.id: a for a in (actions or [])}

    def on_mount(self) -> None:
        """Setup columns after mounting."""
        self._setup_columns()
        self._populate_rows()

    def _setup_columns(self) -> None:
        """Define consistent columns."""
        if len(self.columns) > 0:
            return  # Columns already set up

        columns = [
            "Name",
            "Category",
            "Range",
            "Targeting",
            "Info",
        ]
        for name in columns:
            self.add_column(name)

    def watch_actions(self) -> None:
        """Called automatically when actions changes."""
        if self.is_mounted:
            self._populate_rows()

    def _populate_rows(self) -> None:
        """Populate table rows with action data."""
        # Clear existing rows
        self.clear()

        # Add rows for each action
        for a in sorted(self.actions.values(), key=lambda x: x.name):
            self.add_row(
                f"[bold]{a.name}[/bold]",
                a.category.value,
                f"{a.range} m",
                a.targeting.value,
                self._info_for_action(a),
                key=a.id,
            )

    def update_actions(self, actions: list[Action]) -> None:
        """Update the table with new actions."""
        self.actions = {a.id: a for a in actions}  # Triggers watch_actions

    def _info_for_action(self, action: Action) -> str:
        """Build the info field dynamically depending on subclass."""
        info = ""

        if isinstance(action, AttackAction):
            info = f"{action.hits} hit(s) for {action.damage_dice} {action.damage_type.value} damage"

        elif isinstance(action, AttackSpellAction):
            info = (
                f"Lv {action.level.value}, {action.hits} hit(s) for "
                f"{action.damage_dice} {action.damage_type.value} damage"
            )

        elif isinstance(action, SupportSpellAction):
            info = f"Lv {action.level.value}"

        elif hasattr(action, "status_effects"):
            eff = ", ".join(e.type.value for e in action.status_effects)
            info += f" (+ {eff})"

        return info or "-"


    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """Open a modal when a cell is clicked."""
        action_id = event.cell_key.row_key.value
        action = self.actions.get(action_id or "")
        if action:
            self.app.push_screen(ActionInfoModal(action))


class CharacterSheet(Static):
    """Display a character sheet that reactively updates when character changes."""

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


class CharacterPanel(Static):
    """Display character sheet with dynamic character tabs."""

    def compose(self) -> ComposeResult:
        yield Tabs(id="character-tabs")
        yield ContentSwitcher(id="character-switcher")

    def update_state(self, state: State) -> None:
        """Rebuild tabs and character sheet given the current state."""
        tabs = self.query_one("#character-tabs", Tabs)
        switcher = self.query_one("#character-switcher", ContentSwitcher)

        # Collect existing IDs
        existing_tab_ids = {tab.id for tab in tabs.query("Tab")}
        current_char_ids = set(state.characters.keys())

        # Remove tabs/sheets for characters no longer in state
        for tab_id in existing_tab_ids:
            if tab_id not in current_char_ids:
                # Remove the tab
                tab = tabs.query_one(f"#{tab_id}", Tab)
                tab.remove()

                # Remove the character sheet
                sheet = switcher.query_one(f"#{tab_id}", CharacterSheet)
                sheet.remove()

        # Refresh existing tab IDs after removals
        existing_tab_ids = {tab.id for tab in tabs.query("Tab")}

        for cid, char in state.characters.items():
            if cid not in existing_tab_ids:
                # New character - add tab and sheet
                tab = Tab(label=char.name, id=cid)
                tabs.add_tab(tab)

                sheet = CharacterSheet(char)
                switcher.mount(sheet)
                switcher.current = char.id
            else:
                # Existing character - update the sheet (reactive update)
                sheet = switcher.query_one(f"#{cid}", CharacterSheet)
                sheet.update_character(char)

        if state.turn_order:
            switcher.current = state.current_actor.id
            tabs.active = state.current_actor.id

    @on(Tabs.TabActivated, "#character-tabs")
    def handle_tab_switch(self, event: Tabs.TabActivated) -> None:
        """Switch the content when a tab is activated."""
        switcher = self.query_one("#character-switcher", ContentSwitcher)
        switcher.current = event.tab.id