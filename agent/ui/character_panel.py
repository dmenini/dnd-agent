from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.events import Key
from textual.screen import ModalScreen
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
    def action_dismiss(self, _: Key) -> None:
        """Close modal on any key press."""
        self.dismiss()


class ActionsSummaryTable(DataTable):
    """A compact summary table of all actions with minimal info."""

    def __init__(self, actions: list[Action]) -> None:
        super().__init__()
        self.actions = {a.id: a for a in actions}
        self._setup_columns()
        self._populate_rows(actions)

    def _setup_columns(self) -> None:
        """Define consistent columns."""
        columns = [
            "Name",
            "Category",
            "Range",
            "Targeting",
            "Info",
        ]
        for name in columns:
            self.add_column(name)

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

        elif getattr(action, "status_effects", None):
            eff = ", ".join(e.type.value for e in action.status_effects)
            info += f" (+ {eff})"

        return info or "-"

    def _populate_rows(self, actions: list[Action]) -> None:
        """Add sorted rows to the table."""
        for a in sorted(actions, key=lambda x: x.name):
            self.add_row(
                f"[bold]{a.name}[/bold]",
                a.category.value,
                f"{a.range} m",
                a.targeting.value,
                self._info_for_action(a),
                key=a.id,
            )

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """Open a modal when a cell is clicked."""
        action_id = event.cell_key.row_key.value
        action = self.actions.get(action_id)
        if action:
            self.app.push_screen(ActionInfoModal(action))


class CharacterSheet(Static):
    def __init__(self, char: Character, **kwargs: Any) -> None:
        super().__init__(id=char.id, **kwargs)
        self.char = char

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Markdown(f"## Character {self.char}\n")
            yield Markdown("## Available Actions\n\n")
            yield ActionsSummaryTable(actions=self.char.get_available_actions().values())


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

        for cid, char in state.characters.items():
            if cid not in existing_tab_ids:
                tab = Tab(label=char.name, id=cid)
                tabs.add_tab(tab)

                sheet = CharacterSheet(char)
                switcher.mount(sheet)
                switcher.current = char.id

        if state.turn_order:
            switcher.current = state.current_actor.id
            tabs.active = state.current_actor.id

    @on(Tabs.TabActivated, "#character-tabs")
    def handle_tab_switch(self, event: Tabs.TabActivated) -> None:
        switcher = self.query_one("#character-switcher", ContentSwitcher)
        switcher.current = event.tab.id
