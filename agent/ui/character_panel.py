from rich.console import Group
from rich.markdown import Markdown
from textual.widgets import Static

from agent.actions.render import render_actions_summary
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
            render_actions_summary(list(actor.get_available_actions().values())),
        )
        self.update(renderable)
