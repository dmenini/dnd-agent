from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import ContentSwitcher, Markdown, Static, Tab, Tabs

from agent.actions.render import render_actions_summary
from agent.character.character import Character
from agent.models.state import State


class CharacterSheet(Static):
    def __init__(self, char: Character, **kwargs: Any) -> None:
        super().__init__(id=char.id, **kwargs)
        self.char = char

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Markdown(f"## Character {self.char}\n")
            yield Markdown("---\n")
            yield Markdown("## Available Actions\n\n")
            yield Static(render_actions_summary(list(self.char.get_available_actions().values())))


class CharacterPanel(Static):
    """Right-hand side: character sheet with dynamic character tabs."""

    def compose(self) -> ComposeResult:
        """Compose layout with Tabs and ContentSwitcher."""
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

    @on(Tabs.TabActivated, "#character-tabs")
    def handle_tab_switch(self, event: Tabs.TabActivated) -> None:
        """Switch or reset when clicking a tab."""

        switcher = self.query_one("#character-switcher", ContentSwitcher)
        switcher.current = event.tab.id
