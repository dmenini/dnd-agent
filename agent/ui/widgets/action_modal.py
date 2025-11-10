from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.events import Key
from textual.screen import ModalScreen, ScreenResultType
from textual.widgets import Footer, Static

from agent.actions.base import Action


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


def render_action(action: Action, max_width: int = 50) -> Panel:
    """Render a single Action or subclass as a formatted Rich panel."""

    header = f"[bold]{action.name}[/bold]"
    desc = Text(action.description + "\n", style="white")

    # Base info table
    table = Table.grid(expand=False, padding=(0, 1, 0, 2))  # top, right, bottom, left
    table.add_column(style="dim", no_wrap=True)
    table.add_column()

    table.add_row("ID", str(action.id))
    table.add_row("Type", str(action.type.value))
    table.add_row("Category", str(action.category.value))
    table.add_row("Targeting", str(action.targeting.value))
    table.add_row("Hits", str(action.hits))
    table.add_row("Range", f"{action.range} m")

    damage = getattr(action, "damage_dice", None)
    damage_type = getattr(action, "damage_type", None)
    table.add_row("Damage", f"{damage} {damage_type.value}" if damage and damage_type else "-")

    stat = getattr(action, "ability", None)
    table.add_row("Stat", stat.value if stat else "-")

    effects = ", ".join([e.type.value for e in getattr(action, "status_effects", [])]) or "-"
    table.add_row("Effects", effects)

    level = getattr(action, "level", None)
    table.add_row("Spell Level", f"Level {level.value}" if level else "-")

    # Group description + table
    content = Group(desc, table)

    return Panel(
        content,
        title=header,
        border_style="bright_blue",
        padding=(1, 2),
        expand=False,
        width=max_width,
    )
