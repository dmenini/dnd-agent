from textual.app import ComposeResult
from textual.containers import Center, VerticalScroll
from textual.widgets import Markdown, Static

from agent.models.map import GameMap
from agent.models.state import State


class MapPanel(Static):
    """Display map panel."""

    def compose(self) -> ComposeResult:
        """Build static structure of the panel."""
        # Containers for sections; these can be updated later
        with VerticalScroll(id="map-container"):
            yield Markdown("# Map Overview", id="map-title")
            with Center(id="map-center"):
                yield Static("", id="map-content")
            yield Markdown("", id="character-title")
            yield Markdown("", id="character-list")

    def update_state(self, state: State) -> None:
        """Update the map display according to the current state."""
        map_content = self.query_one("#map-content", Static)
        character_title = self.query_one("#character-title", Markdown)
        character_list = self.query_one("#character-list", Markdown)

        if not state.map:
            empty = GameMap(width=10, height=10, map="")
            map_content.update(str(empty))
            character_title.update("")
            character_list.update("")
            return

        map_content.update(str(state.map))

        if state.turn_order:
            character_title.update("### Visible Characters")
            character_list.update(self._format_characters(state))
        else:
            character_title.update("")
            character_list.update("")

    def _format_characters(self, state: State) -> str:
        lines = []
        actor = state.current_actor
        visible_characters = state.visible_characters
        for c in visible_characters:
            dist = state.map.distance(actor.pos, c.pos)  # type: ignore[union-attr]
            los = actor.los_distance(c.pos)
            effects = ", ".join(str(e) for e in c.status_effects) or "None"
            lines.append(
                f"- {c.icon} ID={c.id}, name={c.name} (HP {c.attributes.hp}/{c.max_hp}) "
                f"at ({c.pos.x}, {c.pos.y}) facing {c.pos.direction}, distance={dist}m, LoS={los}m, effects={effects}"
            )
        return "\n".join(lines) or "- No one in sight, try to explore the map.\n"
