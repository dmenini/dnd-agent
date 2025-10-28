from rich.console import Group
from rich.markdown import Markdown
from rich.text import Text
from textual.widgets import Static

from agent.actions.render import render_actions_summary
from agent.character.character import Character
from agent.models.map import GameMap
from agent.models.state import State


class CharacterPanel(Static):
    """Right-hand side: character sheet."""

    def update_state(self, state: State) -> None:
        if not state.turn_order:
            self.update("Characters not ready")
            return

        actor = state.current_actor
        renderable = Group(
            Markdown(f"## Character {actor}\n", justify="center", style="cyan"),
            Markdown("---\n"),
            Markdown("## Available Actions\n\n", style="cyan"),
            render_actions_summary(actor.get_available_actions().values()),
            Markdown("---\n"),
            Markdown("## Map Overview\n", style="cyan"),
            Text(str(state.map), justify="center", style="cyan"),
            Markdown("Visible Characters:\n", style="cyan"),
            Markdown(f"{self.format_characters(state.visible_characters, state.map, actor)}\n", style="cyan"),
        )
        self.update(renderable)

    def format_characters(self, visible_characters: list[Character], game_map: GameMap, actor: Character) -> str:
        lines = []
        for c in visible_characters:
            dist = game_map.distance(actor.pos, c.pos)
            los = actor.los_distance(c.pos)
            effects = ", ".join(str(e) for e in c.status_effects) or "None"
            lines.append(
                f"- {c.icon} ID={c.id}, name={c.name} (HP {c.attributes.hp}/{c.max_hp}) "
                f"at ({c.pos.x}, {c.pos.y}) facing {c.pos.direction}, distance={dist}m, LoS={los}m, effects={effects}"
            )
        return "\n".join(lines) or "- No one in sight, try to explore the map.\n"
