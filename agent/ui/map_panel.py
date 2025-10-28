from rich.console import Group
from rich.markdown import Markdown
from rich.text import Text
from textual.widgets import Static

from agent.models.state import State


class MapPanel(Static):
    """Top-left: the map."""

    def update_state(self, state: State) -> None:
        if state.map and state.turn_order:
            renderable = Group(
                Markdown("## Map Overview\n", style="cyan"),
                Text(str(state.map), justify="center", style="cyan"),
                Markdown("Visible Characters:\n", style="cyan"),
                Markdown(f"{self.format_characters(state)}\n", style="cyan"),
            )
            self.update(renderable)

    def format_characters(self, state: State) -> str:
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
